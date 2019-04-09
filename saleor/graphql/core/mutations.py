from itertools import chain
from textwrap import dedent

import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import (
    NON_FIELD_ERRORS, ImproperlyConfigured, ValidationError)
from django.db.models.fields.files import FileField
from graphene.types.mutation import MutationOptions
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError
from graphql_jwt import ObtainJSONWebToken, Verify
from graphql_jwt.exceptions import JSONWebTokenError, PermissionDenied

from ...account import models
from ..account.types import User
from ..utils import get_nodes
from .types import Error, Upload
from .utils import snake_to_camel_case

registry = get_global_registry()


def get_model_name(model):
    """Return name of the model with first letter lowercase."""
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


def get_output_fields(model, return_field_name):
    """Return mutation output field for model instance."""
    model_type = registry.get_type_for_model(model)
    if not model_type:
        raise ImproperlyConfigured(
            'Unable to find type for model %s in graphene registry' %
            model.__name__)
    fields = {return_field_name: graphene.Field(model_type)}
    return fields


def validation_error_to_error_type(validation_error: ValidationError) -> list:
    """Convert a ValidationError into a list of Error types."""
    err_list = []
    if hasattr(validation_error, 'error_dict'):
        # convert field errors
        for field, field_errors in validation_error.message_dict.items():
            for err in field_errors:
                field = None if field == NON_FIELD_ERRORS else snake_to_camel_case(
                    field)
                err_list.append(Error(field=field, message=err))
    else:
        # convert non-field errors
        for err in validation_error.error_list:
            err_list.append(Error(message=err.message))
    return err_list


class ModelMutationOptions(MutationOptions):
    exclude = None
    model = None
    return_field_name = None


class BaseMutation(graphene.Mutation):
    errors = graphene.List(
        graphene.NonNull(Error),
        description='List of errors that occurred executing the mutation.')

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, description=None, **options):
        if not description:
            raise ImproperlyConfigured('No description provided in Meta')
        description = dedent(description)
        super().__init_subclass_with_meta__(description=description, **options)

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def get_node_or_error(cls, info, node_id, field='id', only_type=None):
        if not node_id:
            return None

        try:
            node = graphene.Node.get_node_from_global_id(
                info, node_id, only_type)
        except (AssertionError, GraphQLError) as e:
            raise ValidationError({field: str(e)})
        else:
            if node is None:
                raise ValidationError({
                    field: "Couldn't resolve to a node: %s" % node_id})
        return node

    @classmethod
    def get_nodes_or_error(cls, ids, field, only_type=None):
        try:
            instances = get_nodes(ids, only_type)
        except GraphQLError as e:
            raise ValidationError({field: str(e)})
        return instances

    @classmethod
    def clean_instance(cls, instance):
        """Clean the instance that was created using the input data.

        Once an instance is created, this method runs `full_clean()` to perform
        model validation.
        """
        try:
            instance.full_clean()
        except ValidationError as error:
            if hasattr(cls._meta, 'exclude'):
                # Ignore validation errors for fields that are specified as
                # excluded.
                new_error_dict = {}
                for field, errors in error.error_dict.items():
                    if field not in cls._meta.exclude:
                        new_error_dict[field] = errors
                error.error_dict = new_error_dict

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
            if any([not f.editable, isinstance(f, models.AutoField),
                    f.name not in cleaned_data]):
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
    def user_is_allowed(cls, user, input):
        """Determine whether user has rights to perform this mutation.

        Default implementation assumes that user is allowed to perform any
        mutation. By overriding this method, you can restrict access to it.
        `user` is the User instance associated with the request and `input` is
        the input data provided as mutation arguments.
        """
        return True

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        try:
            response = cls.perform_mutation(root, info, **data)
            if response.errors is None:
                response.errors = []
            return response
        except ValidationError as e:
            errors = validation_error_to_error_type(e)
            return cls(errors=errors)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        pass


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
            **options):
        if not model:
            raise ImproperlyConfigured('model is required for ModelMutation')
        if not _meta:
            _meta = ModelMutationOptions(cls)

        if exclude is None:
            exclude = []

        if not return_field_name:
            return_field_name = get_model_name(model)
        if arguments is None:
            arguments = {}
        fields = get_output_fields(model, return_field_name)

        _meta.model = model
        _meta.return_field_name = return_field_name
        _meta.exclude = exclude
        super().__init_subclass_with_meta__(_meta=_meta, **options)
        cls._update_mutation_arguments_and_fields(
            arguments=arguments, fields=fields)

    @classmethod
    def clean_input(cls, info, instance, input):
        """Clean input data received from mutation arguments.

        Fields containing IDs or lists of IDs are automatically resolved into
        model instances. `instance` argument is the model instance the mutation
        is operating on (before setting the input data). `input` is raw input
        data the mutation receives.

        Override this method to provide custom transformations of incoming
        data.
        """

        def is_list_of_ids(field):
            return (
                    isinstance(field.type, graphene.List)
                    and field.type.of_type == graphene.ID)

        def is_id_field(field):
            return (
                    field.type == graphene.ID
                    or isinstance(field.type, graphene.NonNull)
                    and field.type.of_type == graphene.ID)

        def is_upload_field(field):
            if hasattr(field.type, 'of_type'):
                return field.type.of_type == Upload
            return field.type == Upload

        InputCls = getattr(cls.Arguments, 'input')
        cleaned_input = {}

        for field_name, field in InputCls._meta.fields.items():
            if field_name in input:
                value = input[field_name]

                # handle list of IDs field
                if value is not None and is_list_of_ids(field):
                    instances = cls.get_nodes_or_error(
                        value, field_name) if value else []
                    cleaned_input[field_name] = instances

                # handle ID field
                elif value is not None and is_id_field(field):
                    instance = cls.get_node_or_error(info, value, field_name)
                    cleaned_input[field_name] = instance

                # handle uploaded files
                elif value is not None and is_upload_field(field):
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
            if not hasattr(f, 'save_form_data'):
                continue
            if f.name in cleaned_data and cleaned_data[f.name] is not None:
                f.save_form_data(instance, cleaned_data[f.name])

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(**{cls._meta.return_field_name: instance, 'errors': []})

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

    @classmethod
    def get_instance(cls, info, **data):
        object_id = data.get('id')
        if object_id:
            model_type = registry.get_type_for_model(cls._meta.model)
            instance = cls.get_node_or_error(
                info, object_id, only_type=model_type)
        else:
            instance = cls._meta.model()
        return instance

    @classmethod
    def perform_mutation(cls, root, info, **data):
        """Perform model mutation.

        Depending on the input data, `mutate` either creates a new instance or
        updates an existing one. If `id` arugment is present, it is assumed
        that this is an "update" mutation. Otherwise, a new instance is
        created based on the model associated with this mutation.
        """
        instance = cls.get_instance(info, **data)
        input_data = data.get('input')
        cleaned_input = cls.clean_input(info, instance, input_data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
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
    def perform_mutation(cls, root, info, **data):
        """Perform a mutation that deletes a model instance."""
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        node_id = data.get('id')
        model_type = registry.get_type_for_model(cls._meta.model)
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
        required=True, description='Returns how many objects were affected.')

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, model=None, _meta=None, **kwargs):
        if not model:
            raise ImproperlyConfigured('model is required for bulk mutation')
        if not _meta:
            _meta = ModelMutationOptions(cls)
        _meta.model = model

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)

    @classmethod
    def user_is_allowed(cls, user, ids):
        """Determine whether user has rights to perform this mutation.

        Default implementation assumes that user is allowed to perform any
        mutation. By overriding this method, you can restrict access to it.
        `user` is the User instance associated with the request and `input` is
        the input data provided as mutation arguments.
        """
        return True

    @classmethod
    def bulk_action(cls, instances):
        """Implement action performed on list of instances"""
        raise NotImplementedError

    @classmethod
    def perform_mutation(cls, root, info, ids):
        """Perform a mutation that deletes a list of model instances."""
        clean_instances, errors = [], {}
        model_type = registry.get_type_for_model(cls._meta.model)
        instances = cls.get_nodes_or_error(ids, 'id', model_type)
        for instance, node_id in zip(instances, ids):
            instance_errors = []

            # catch individual validation errors to raise them later as
            # a single error
            try:
                cls.clean_instance(info, instance)
            except ValidationError as e:
                msg = '. '.join(e.messages)
                instance_errors.append(msg)

            if not instance_errors:
                clean_instances.append(instance)
            else:
                instance_errors_msg = '. '.join(instance_errors)
                ValidationError({
                    node_id: instance_errors_msg}).update_error_dict(errors)

        if errors:
            errors = ValidationError(errors)
        count = len(clean_instances)
        cls.bulk_action(clean_instances)
        return count, errors

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        count, errors = cls.perform_mutation(root, info, **data)
        if errors:
            errors = validation_error_to_error_type(errors)
        return cls(errors=errors, count=count)


class ModelBulkDeleteMutation(BaseBulkMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        """Perform additional logic before deleting the model instance.

        Override this method to raise custom validation error and abort
        the deletion process.
        """

    @classmethod
    def bulk_action(cls, instances):
        for instance in instances:
            instance.delete()


class CreateToken(ObtainJSONWebToken):
    """Mutation that authenticates a user and returns token and user data.

    It overrides the default graphql_jwt.ObtainJSONWebToken to wrap potential
    authentication errors in our Error type, which is consistent to how rest of
    the mutation works.
    """

    errors = graphene.List(Error, required=True)
    user = graphene.Field(User)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            result = super().mutate(root, info, **kwargs)
        except JSONWebTokenError as e:
            return CreateToken(errors=[Error(message=str(e))])
        else:
            return result

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user, errors=[])


class VerifyToken(Verify):
    """Mutation that confirm if token is valid and also return user data."""

    user = graphene.Field(User)

    def resolve_user(self, info, **kwargs):
        username_field = get_user_model().USERNAME_FIELD
        kwargs = {username_field: self.payload.get(username_field)}
        return models.User.objects.get(**kwargs)
