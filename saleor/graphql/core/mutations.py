from itertools import chain
from typing import Tuple, Union

import graphene
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ImproperlyConfigured,
    ValidationError,
)
from django.core.files.storage import default_storage
from django.db.models.fields.files import FileField
from graphene import ObjectType
from graphene.types.mutation import MutationOptions
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError

from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions
from ..decorators import staff_member_or_app_required
from ..utils import get_nodes
from .types import Error, File, Upload
from .types.common import UploadError
from .utils import from_global_id_strict_type, snake_to_camel_case
from .utils.error_codes import get_error_code_from_error

registry = get_global_registry()


def get_model_name(model):
    """Return name of the model with first letter lowercase."""
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


def get_error_fields(error_type_class, error_type_field):
    return {
        error_type_field: graphene.Field(
            graphene.List(
                graphene.NonNull(error_type_class),
                description="List of errors that occurred executing the mutation.",
            ),
            default_value=[],
            required=True,
        )
    }


def validation_error_to_error_type(validation_error: ValidationError) -> list:
    """Convert a ValidationError into a list of Error types."""
    err_list = []
    if hasattr(validation_error, "error_dict"):
        # convert field errors
        for field, field_errors in validation_error.error_dict.items():
            field = None if field == NON_FIELD_ERRORS else snake_to_camel_case(field)
            for err in field_errors:
                err_list.append(
                    (
                        Error(field=field, message=err.messages[0]),
                        get_error_code_from_error(err),
                        err.params,
                    )
                )
    else:
        # convert non-field errors
        for err in validation_error.error_list:
            err_list.append(
                (
                    Error(message=err.messages[0]),
                    get_error_code_from_error(err),
                    err.params,
                )
            )
    return err_list


class ModelMutationOptions(MutationOptions):
    exclude = None
    model = None
    return_field_name = None


class BaseMutation(graphene.Mutation):
    errors = graphene.List(
        graphene.NonNull(Error),
        description="List of errors that occurred executing the mutation.",
        deprecation_reason=(
            "Use typed errors with error codes. This field will be removed after "
            "2020-07-31."
        ),
        required=True,
    )

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        description=None,
        permissions: Tuple = None,
        _meta=None,
        error_type_class=None,
        error_type_field=None,
        errors_mapping=None,
        **options,
    ):
        if not _meta:
            _meta = MutationOptions(cls)

        if not description:
            raise ImproperlyConfigured("No description provided in Meta")

        if isinstance(permissions, str):
            permissions = (permissions,)

        if permissions and not isinstance(permissions, tuple):
            raise ImproperlyConfigured(
                "Permissions should be a tuple or a string in Meta"
            )

        _meta.permissions = permissions
        _meta.error_type_class = error_type_class
        _meta.error_type_field = error_type_field
        _meta.errors_mapping = errors_mapping
        super().__init_subclass_with_meta__(
            description=description, _meta=_meta, **options
        )
        if error_type_class and error_type_field:
            cls._meta.fields.update(
                get_error_fields(error_type_class, error_type_field)
            )

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def get_node_by_pk(
        cls, info, graphene_type: ObjectType, pk: Union[int, str], qs=None
    ):
        """Attempt to resolve a node from the given internal ID.

        Whether by using the provided query set object or by calling type's get_node().
        """
        if qs is not None:
            return qs.filter(pk=pk).first()
        get_node = getattr(graphene_type, "get_node", None)
        if get_node:
            return get_node(info, pk)
        return None

    @classmethod
    def get_node_or_error(cls, info, node_id, field="id", only_type=None, qs=None):
        if not node_id:
            return None

        try:
            if only_type is not None:
                pk = from_global_id_strict_type(node_id, only_type, field=field)
            else:
                # FIXME: warn when supplied only_type is None?
                only_type, pk = graphene.Node.from_global_id(node_id)

            if isinstance(only_type, str):
                only_type = info.schema.get_type(only_type).graphene_type

            node = cls.get_node_by_pk(info, graphene_type=only_type, pk=pk, qs=qs)
        except (AssertionError, GraphQLError) as e:
            raise ValidationError(
                {field: ValidationError(str(e), code="graphql_error")}
            )
        else:
            if node is None:
                raise ValidationError(
                    {
                        field: ValidationError(
                            "Couldn't resolve to a node: %s" % node_id, code="not_found"
                        )
                    }
                )
        return node

    @classmethod
    def get_nodes_or_error(cls, ids, field, only_type=None, qs=None):
        try:
            instances = get_nodes(ids, only_type, qs=qs)
        except GraphQLError as e:
            raise ValidationError(
                {field: ValidationError(str(e), code="graphql_error")}
            )
        return instances

    @staticmethod
    def remap_error_fields(validation_error, field_map):
        """Rename validation_error fields accoring to provided field_map.

        Skips renaming fields from field_map that are not on validation_error.
        """
        for old_field, new_field in field_map.items():
            try:
                validation_error.error_dict[
                    new_field
                ] = validation_error.error_dict.pop(old_field)
            except KeyError:
                pass

    @classmethod
    def clean_instance(cls, info, instance):
        """Clean the instance that was created using the input data.

        Once an instance is created, this method runs `full_clean()` to perform
        model validation.
        """
        try:
            instance.full_clean()
        except ValidationError as error:
            if hasattr(cls._meta, "exclude"):
                # Ignore validation errors for fields that are specified as
                # excluded.
                new_error_dict = {}
                for field, errors in error.error_dict.items():
                    if field not in cls._meta.exclude:
                        new_error_dict[field] = errors
                error.error_dict = new_error_dict

            if cls._meta.errors_mapping:
                cls.remap_error_fields(error, cls._meta.errors_mapping)

            if error.error_dict:
                raise error

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        """Fill instance fields with cleaned data.

        The `instance` argument is either an empty instance of a already
        existing one which was fetched from the database. `cleaned_data` is
        data to be set in instance fields. Returns `instance` with filled
        fields, but not saved to the database.
        """
        from django.db import models

        opts = instance._meta

        for f in opts.fields:
            if any(
                [
                    not f.editable,
                    isinstance(f, models.AutoField),
                    f.name not in cleaned_data,
                ]
            ):
                continue
            data = cleaned_data[f.name]
            if data is None:
                # We want to reset the file field value when None was passed
                # in the input, but `FileField.save_form_data` ignores None
                # values. In that case we manually pass False which clears
                # the file.
                if isinstance(f, FileField):
                    data = False
                if not f.null:
                    data = f._get_default()
            f.save_form_data(instance, data)
        return instance

    @classmethod
    def check_permissions(cls, context, permissions=None):
        """Determine whether user or app has rights to perform this mutation.

        Default implementation assumes that account is allowed to perform any
        mutation. By overriding this method or defining required permissions
        in the meta-class, you can restrict access to it.

        The `context` parameter is the Context instance associated with the request.
        """
        permissions = permissions or cls._meta.permissions
        if not permissions:
            return True
        if context.user.has_perms(permissions):
            return True
        app = getattr(context, "app", None)
        if app:
            # for now MANAGE_STAFF permission for app is not supported
            if AccountPermissions.MANAGE_STAFF in permissions:
                return False
            return app.has_perms(permissions)
        return False

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        try:
            response = cls.perform_mutation(root, info, **data)
            if response.errors is None:
                response.errors = []
            return response
        except ValidationError as e:
            return cls.handle_errors(e)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        pass

    @classmethod
    def handle_errors(cls, error: ValidationError, **extra):
        errors = validation_error_to_error_type(error)
        return cls.handle_typed_errors(errors, **extra)

    @classmethod
    def handle_typed_errors(cls, errors: list, **extra):
        """Return class instance with errors."""
        if (
            cls._meta.error_type_class is not None
            and cls._meta.error_type_field is not None
        ):
            typed_errors = []
            error_class_fields = set(cls._meta.error_type_class._meta.fields.keys())
            for e, code, params in errors:
                error_instance = cls._meta.error_type_class(
                    field=e.field, message=e.message, code=code
                )
                if params:
                    # If some of the params key overlap with error class fields
                    # attach param value to the error
                    error_fields_in_params = set(params.keys()) & error_class_fields
                    for error_field in error_fields_in_params:
                        setattr(error_instance, error_field, params[error_field])
                typed_errors.append(error_instance)

            extra.update({cls._meta.error_type_field: typed_errors})
        return cls(errors=[e[0] for e in errors], **extra)


class ModelMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        arguments=None,
        model=None,
        exclude=None,
        return_field_name=None,
        _meta=None,
        **options,
    ):
        if not model:
            raise ImproperlyConfigured("model is required for ModelMutation")
        if not _meta:
            _meta = ModelMutationOptions(cls)

        if exclude is None:
            exclude = []

        if not return_field_name:
            return_field_name = get_model_name(model)
        if arguments is None:
            arguments = {}

        _meta.model = model
        _meta.return_field_name = return_field_name
        _meta.exclude = exclude
        super().__init_subclass_with_meta__(_meta=_meta, **options)

        model_type = cls.get_type_for_model()
        if not model_type:
            raise ImproperlyConfigured(
                "Unable to find type for model %s in graphene registry" % model.__name__
            )
        fields = {return_field_name: graphene.Field(model_type)}

        cls._update_mutation_arguments_and_fields(arguments=arguments, fields=fields)

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        """Clean input data received from mutation arguments.

        Fields containing IDs or lists of IDs are automatically resolved into
        model instances. `instance` argument is the model instance the mutation
        is operating on (before setting the input data). `input` is raw input
        data the mutation receives.

        Override this method to provide custom transformations of incoming
        data.
        """

        def is_list_of_ids(field):
            if isinstance(field.type, graphene.List):
                of_type = field.type.of_type
                if isinstance(of_type, graphene.NonNull):
                    of_type = of_type.of_type
                return of_type == graphene.ID
            return False

        def is_id_field(field):
            return (
                field.type == graphene.ID
                or isinstance(field.type, graphene.NonNull)
                and field.type.of_type == graphene.ID
            )

        def is_upload_field(field):
            if hasattr(field.type, "of_type"):
                return field.type.of_type == Upload
            return field.type == Upload

        if not input_cls:
            input_cls = getattr(cls.Arguments, "input")
        cleaned_input = {}

        for field_name, field_item in input_cls._meta.fields.items():
            if field_name in data:
                value = data[field_name]

                # handle list of IDs field
                if value is not None and is_list_of_ids(field_item):
                    instances = (
                        cls.get_nodes_or_error(value, field_name) if value else []
                    )
                    cleaned_input[field_name] = instances

                # handle ID field
                elif value is not None and is_id_field(field_item):
                    instance = cls.get_node_or_error(info, value, field_name)
                    cleaned_input[field_name] = instance

                # handle uploaded files
                elif value is not None and is_upload_field(field_item):
                    value = info.context.FILES.get(value)
                    cleaned_input[field_name] = value

                # handle other fields
                else:
                    cleaned_input[field_name] = value
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        opts = instance._meta
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, "save_form_data"):
                continue
            if f.name in cleaned_data and cleaned_data[f.name] is not None:
                f.save_form_data(instance, cleaned_data[f.name])

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(**{cls._meta.return_field_name: instance, "errors": []})

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

    @classmethod
    def get_type_for_model(cls):
        return registry.get_type_for_model(cls._meta.model)

    @classmethod
    def get_instance(cls, info, **data):
        """Retrieve an instance from the supplied global id.

        The expected graphene type can be lazy (str).
        """
        object_id = data.get("id")
        if object_id:
            model_type = cls.get_type_for_model()
            instance = cls.get_node_or_error(info, object_id, only_type=model_type)
        else:
            instance = cls._meta.model()
        return instance

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        """Perform an action after saving an object and its m2m."""
        pass

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform model mutation.

        Depending on the input data, `mutate` either creates a new instance or
        updates an existing one. If `id` argument is present, it is assumed
        that this is an "update" mutation. Otherwise, a new instance is
        created based on the model associated with this mutation.
        """
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)


class ModelDeleteMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        """Perform additional logic before deleting the model instance.

        Override this method to raise custom validation error and abort
        the deletion process.
        """

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform a mutation that deletes a model instance."""
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        node_id = data.get("id")
        model_type = cls.get_type_for_model()
        instance = cls.get_node_or_error(info, node_id, only_type=model_type)

        if instance:
            cls.clean_instance(info, instance)

        db_id = instance.id
        instance.delete()

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        return cls.success_response(instance)


class BaseBulkMutation(BaseMutation):
    count = graphene.Int(
        required=True, description="Returns how many objects were affected."
    )

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, model=None, _meta=None, **kwargs):
        if not model:
            raise ImproperlyConfigured("model is required for bulk mutation")
        if not _meta:
            _meta = ModelMutationOptions(cls)
        _meta.model = model

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)

    @classmethod
    def clean_instance(cls, info, instance):
        """Perform additional logic.

        Override this method to raise custom validation error and prevent
        bulk action on the instance.
        """

    @classmethod
    def bulk_action(cls, queryset, **kwargs):
        """Implement action performed on queryset."""
        raise NotImplementedError

    @classmethod
    def perform_mutation(cls, _root, info, ids, **data):
        """Perform a mutation that deletes a list of model instances."""
        clean_instance_ids, errors = [], {}
        # Allow to pass empty list for dummy mutation
        if not ids:
            return 0, errors
        instance_model = cls._meta.model
        model_type = registry.get_type_for_model(instance_model)
        instances = cls.get_nodes_or_error(ids, "id", model_type)
        for instance, node_id in zip(instances, ids):
            instance_errors = []

            # catch individual validation errors to raise them later as
            # a single error
            try:
                cls.clean_instance(info, instance)
            except ValidationError as e:
                msg = ". ".join(e.messages)
                instance_errors.append(msg)

            if not instance_errors:
                clean_instance_ids.append(instance.pk)
            else:
                instance_errors_msg = ". ".join(instance_errors)
                ValidationError({node_id: instance_errors_msg}).update_error_dict(
                    errors
                )

        if errors:
            errors = ValidationError(errors)
        count = len(clean_instance_ids)
        if count:
            qs = instance_model.objects.filter(pk__in=clean_instance_ids)
            cls.bulk_action(queryset=qs, **data)
        return count, errors

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        count, errors = cls.perform_mutation(root, info, **data)
        if errors:
            return cls.handle_errors(errors, count=count)

        return cls(errors=errors, count=count)


class ModelBulkDeleteMutation(BaseBulkMutation):
    class Meta:
        abstract = True

    @classmethod
    def bulk_action(cls, queryset):
        queryset.delete()


class FileUpload(BaseMutation):
    uploaded_file = graphene.Field(File)

    class Arguments:
        file = Upload(
            required=True, description="Represents a file in a multipart request."
        )

    class Meta:
        description = (
            "Upload a file. This mutation must be sent as a `multipart` "
            "request. More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        error_type_class = UploadError
        error_type_field = "upload_errors"

    @classmethod
    @staff_member_or_app_required
    def perform_mutation(cls, _root, info, **data):
        file_data = info.context.FILES.get(data["file"])
        path = default_storage.save(file_data._name, file_data.file)

        return FileUpload(
            uploaded_file=File(url=path, content_type=file_data.content_type)
        )
