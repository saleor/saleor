import os
import secrets
from enum import Enum
from itertools import chain
from typing import Iterable, Optional, Tuple, Union
from uuid import UUID

import graphene
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ImproperlyConfigured,
    ValidationError,
)
from django.core.files.storage import default_storage
from django.db.models import Q
from django.db.models.fields.files import FileField
from graphene import ObjectType
from graphene.types.mutation import MutationOptions
from graphql.error import GraphQLError

from ...core.exceptions import PermissionDenied
from ...core.permissions import (
    AuthorizationFilters,
    message_one_of_permissions_required,
    one_of_permissions_or_auth_filter_required,
)
from ..plugins.dataloaders import load_plugin_manager
from ..utils import get_nodes, resolve_global_ids_to_primary_keys
from .context import set_mutation_flag_in_context
from .descriptions import DEPRECATED_IN_3X_FIELD
from .types import (
    TYPES_WITH_DOUBLE_ID_AVAILABLE,
    File,
    NonNullList,
    Upload,
    UploadError,
)
from .utils import from_global_id_or_error, snake_to_camel_case
from .utils.error_codes import get_error_code_from_error


def get_model_name(model):
    """Return name of the model with first letter lowercase."""
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


def get_error_fields(error_type_class, error_type_field, deprecation_reason=None):
    error_field = graphene.Field(
        NonNullList(
            error_type_class,
            description="List of errors that occurred executing the mutation.",
        ),
        default_value=[],
        required=True,
    )
    if deprecation_reason is not None:
        error_field.deprecation_reason = deprecation_reason
    return {error_type_field: error_field}


def validation_error_to_error_type(
    validation_error: ValidationError, error_type_class
) -> list:
    """Convert a ValidationError into a list of Error types."""
    err_list = []
    error_class_fields = set(error_type_class._meta.fields.keys())
    if hasattr(validation_error, "error_dict"):
        # convert field errors
        for field_label, field_errors in validation_error.error_dict.items():
            field = (
                None
                if field_label == NON_FIELD_ERRORS
                else snake_to_camel_case(field_label)
            )
            for err in field_errors:
                error = error_type_class(
                    field=field,
                    message=err.messages[0],
                    code=get_error_code_from_error(err),
                )
                attach_error_params(error, err.params, error_class_fields)
                err_list.append(error)
    else:
        # convert non-field errors
        for err in validation_error.error_list:
            error = error_type_class(
                message=err.messages[0],
                code=get_error_code_from_error(err),
            )
            attach_error_params(error, err.params, error_class_fields)
            err_list.append(error)
    return err_list


def attach_error_params(error, params: Optional[dict], error_class_fields: set):
    if not params:
        return {}
    # If some of the params key overlap with error class fields
    # attach param value to the error
    error_fields_in_params = set(params.keys()) & error_class_fields
    for error_field in error_fields_in_params:
        setattr(error, error_field, params[error_field])


class ModelMutationOptions(MutationOptions):
    exclude = None
    model = None
    object_type = None
    return_field_name = None


class BaseMutation(graphene.Mutation):
    class Meta:
        abstract = True

    @classmethod
    def _validate_permissions(cls, permissions):
        if not permissions:
            return
        if not isinstance(permissions, tuple):
            raise ImproperlyConfigured(
                f"Permissions should be a tuple in Meta class: {permissions}"
            )
        for p in permissions:
            if not isinstance(p, Enum):
                raise ImproperlyConfigured(f"Permission should be an enum: {p}.")

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        auto_permission_message=True,
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

        if not error_type_class:
            raise ImproperlyConfigured("No error_type_class provided in Meta.")

        cls._validate_permissions(permissions)

        _meta.auto_permission_message = auto_permission_message
        _meta.permissions = permissions
        _meta.error_type_class = error_type_class
        _meta.error_type_field = error_type_field
        _meta.errors_mapping = errors_mapping

        if permissions and auto_permission_message:
            permissions_msg = message_one_of_permissions_required(permissions)
            description = f"{description} {permissions_msg}"

        super().__init_subclass_with_meta__(
            description=description, _meta=_meta, **options
        )

        if error_type_field:
            deprecated_msg = f"{DEPRECATED_IN_3X_FIELD} Use `errors` field instead."
            cls._meta.fields.update(
                get_error_fields(
                    error_type_class,
                    error_type_field,
                    deprecated_msg,
                )
            )
        cls._meta.fields.update(get_error_fields(error_type_class, "errors"))

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def _get_node_by_pk(
        cls, info, graphene_type: ObjectType, pk: Union[int, str], qs=None
    ):
        """Attempt to resolve a node from the given internal ID.

        Whether by using the provided query set object or by calling type's get_node().
        """
        if qs is not None:
            lookup = Q(pk=pk)
            if pk is not None and str(graphene_type) in TYPES_WITH_DOUBLE_ID_AVAILABLE:
                # This is temporary solution that allows fetching objects with use of
                # new and old id.
                try:
                    UUID(str(pk))
                except ValueError:
                    lookup = (
                        Q(number=pk) & Q(use_old_id=True)
                        if str(graphene_type) == "Order"
                        else Q(old_id=pk) & Q(old_id__isnull=False)
                    )
            return qs.filter(lookup).first()
        get_node = getattr(graphene_type, "get_node", None)
        if get_node:
            return get_node(info, pk)
        return None

    @classmethod
    def get_global_id_or_error(
        cls, id: str, only_type: Union[ObjectType, str] = None, field: str = "id"
    ):
        try:
            _object_type, pk = from_global_id_or_error(id, only_type, raise_error=True)
        except GraphQLError as e:
            raise ValidationError(
                {field: ValidationError(str(e), code="graphql_error")}
            )
        return pk

    @classmethod
    def get_node_or_error(
        cls, info, node_id, field="id", only_type=None, qs=None, code="not_found"
    ):
        if not node_id:
            return None

        try:
            object_type, pk = from_global_id_or_error(
                node_id, only_type, raise_error=True
            )

            if isinstance(object_type, str):
                object_type = info.schema.get_type(object_type).graphene_type

            node = cls._get_node_by_pk(info, graphene_type=object_type, pk=pk, qs=qs)
        except (AssertionError, GraphQLError) as e:
            raise ValidationError(
                {field: ValidationError(str(e), code="graphql_error")}
            )
        else:
            if node is None:
                raise ValidationError(
                    {
                        field: ValidationError(
                            "Couldn't resolve to a node: %s" % node_id, code=code
                        )
                    }
                )
        return node

    @classmethod
    def get_global_ids_or_error(
        cls,
        ids: Iterable[str],
        only_type: Union[ObjectType, str] = None,
        field: str = "ids",
    ):
        try:
            _nodes_type, pks = resolve_global_ids_to_primary_keys(
                ids, only_type, raise_error=True
            )
        except GraphQLError as e:
            raise ValidationError(
                {field: ValidationError(str(e), code="graphql_error")}
            )
        return pks

    @classmethod
    def get_nodes_or_error(cls, ids, field, only_type=None, qs=None, schema=None):
        try:
            instances = get_nodes(ids, only_type, qs=qs, schema=schema)
        except GraphQLError as e:
            raise ValidationError(
                {field: ValidationError(str(e), code="graphql_error")}
            )
        return instances

    @staticmethod
    def remap_error_fields(validation_error, field_map):
        """Rename validation_error fields according to provided field_map.

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
        all_permissions = permissions or cls._meta.permissions
        if not all_permissions:
            return True

        return one_of_permissions_or_auth_filter_required(context, all_permissions)

    @classmethod
    def mutate(cls, root, info, **data):
        set_mutation_flag_in_context(info.context)

        if not cls.check_permissions(info.context):
            raise PermissionDenied(permissions=cls._meta.permissions)
        manager = load_plugin_manager(info.context)
        result = manager.perform_mutation(
            mutation_cls=cls, root=root, info=info, data=data
        )
        if result is not None:
            return result

        try:
            response = cls.perform_mutation(root, info, **data)
            if response.errors is None:
                response.errors = []
            return response
        except ValidationError as e:
            return cls.handle_errors(e)

    @classmethod
    def perform_mutation(cls, _root, _info, **data):
        pass

    @classmethod
    def handle_errors(cls, error: ValidationError, **extra):
        error_list = validation_error_to_error_type(error, cls._meta.error_type_class)
        return cls.handle_typed_errors(error_list, **extra)

    @classmethod
    def handle_typed_errors(cls, errors: list, **extra):
        """Return class instance with errors."""
        if cls._meta.error_type_field is not None:
            extra.update({cls._meta.error_type_field: errors})
        return cls(errors=errors, **extra)


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
        object_type=None,
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
        _meta.object_type = object_type
        _meta.return_field_name = return_field_name
        _meta.exclude = exclude
        super().__init_subclass_with_meta__(_meta=_meta, **options)

        model_type = cls.get_type_for_model()
        if not model_type:
            raise ImproperlyConfigured(
                f"GraphQL type for model {cls._meta.model.__name__} could not be "
                f"resolved for {cls.__name__}"
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
                        cls.get_nodes_or_error(value, field_name, schema=info.schema)
                        if value
                        else []
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
        if not cls._meta.object_type:
            raise ImproperlyConfigured(
                f"Either GraphQL type for model {cls._meta.model.__name__} needs to be "
                f"specified on object_type option or {cls.__name__} needs to define "
                "custom get_type_for_model() method."
            )

        return cls._meta.object_type

    @classmethod
    def get_instance(cls, info, **data):
        """Retrieve an instance from the supplied global id.

        The expected graphene type can be lazy (str).
        """
        object_id = data.get("id")
        qs = data.get("qs")
        if object_id:
            model_type = cls.get_type_for_model()
            instance = cls.get_node_or_error(
                info, object_id, only_type=model_type, qs=qs
            )
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
        cls.post_save_action(info, instance, None)
        return cls.success_response(instance)


class BaseBulkMutation(BaseMutation):
    count = graphene.Int(
        required=True, description="Returns how many objects were affected."
    )

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls, model=None, object_type=None, _meta=None, **kwargs
    ):
        if not model:
            raise ImproperlyConfigured("model is required for bulk mutation")
        if not _meta:
            _meta = ModelMutationOptions(cls)
        _meta.model = model
        _meta.object_type = object_type

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)

    @classmethod
    def get_type_for_model(cls):
        if not cls._meta.object_type:
            raise ImproperlyConfigured(
                f"Either GraphQL type for model {cls._meta.model.__name__} needs to be "
                f"specified on object_type option or {cls.__name__} needs to define "
                "custom get_type_for_model() method."
            )

        return cls._meta.object_type

    @classmethod
    def clean_instance(cls, info, instance):
        """Perform additional logic.

        Override this method to raise custom validation error and prevent
        bulk action on the instance.
        """

    @classmethod
    def bulk_action(cls, info, queryset, **kwargs):
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
        model_type = cls.get_type_for_model()
        if not model_type:
            raise ImproperlyConfigured(
                f"GraphQL type for model {cls._meta.model.__name__} could not be "
                f"resolved for {cls.__name__}"
            )

        try:
            instances = cls.get_nodes_or_error(
                ids, "id", model_type, schema=info.schema
            )
        except ValidationError as error:
            return 0, error
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
            cls.bulk_action(info=info, queryset=qs, **data)
        return count, errors

    @classmethod
    def mutate(cls, root, info, **data):
        set_mutation_flag_in_context(info.context)
        if not cls.check_permissions(info.context):
            raise PermissionDenied(permissions=cls._meta.permissions)
        manager = load_plugin_manager(info.context)
        result = manager.perform_mutation(
            mutation_cls=cls, root=root, info=info, data=data
        )
        if result is not None:
            return result

        count, errors = cls.perform_mutation(root, info, **data)
        if errors:
            return cls.handle_errors(errors, count=count)

        return cls(errors=errors, count=count)


class ModelBulkDeleteMutation(BaseBulkMutation):
    class Meta:
        abstract = True

    @classmethod
    def bulk_action(cls, info, queryset):
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
        permissions = (
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        file_data = info.context.FILES.get(data["file"])

        # add unique text fragment to the file name to prevent file overriding
        file_name, format = os.path.splitext(file_data._name)
        hash = secrets.token_hex(nbytes=4)
        new_name = f"file_upload/{file_name}_{hash}{format}"

        path = default_storage.save(new_name, file_data.file)

        return FileUpload(
            uploaded_file=File(url=path, content_type=file_data.content_type)
        )
