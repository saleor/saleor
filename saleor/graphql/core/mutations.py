from itertools import chain

import graphene
from django.core.exceptions import ImproperlyConfigured, ValidationError
from graphene.types.mutation import MutationOptions
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError
from graphql_jwt import ObtainJSONWebToken, Verify
from graphql_jwt.exceptions import GraphQLJWTError, PermissionDenied

from ...account import models
from ..account.types import User
from ..file_upload.types import Upload
from ..utils import get_nodes
from .types.common import Error
from .utils import snake_to_camel_case

registry = get_global_registry()


def get_model_name(model):
    """Return name of the model with first letter lowercase."""
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


def get_output_fields(model, return_field_name):
    """Return mutation output field for model instance."""
    model_type = registry.get_type_for_model(model)
    fields = {return_field_name: graphene.Field(model_type)}
    return fields


class ModelMutationOptions(MutationOptions):
    exclude = None
    model = None
    return_field_name = None


class BaseMutation(graphene.Mutation):
    errors = graphene.List(
        Error,
        description='List of errors that occurred executing the mutation.')

    class Meta:
        abstract = True

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def add_error(cls, errors, field, message):
        """Add a mutation user error.

        `errors` is the list of errors that happened during the execution of
        the mutation. `field` is the name of an input field the error is
        related to. `None` value is allowed and it indicates that the error
        is general and is not related to any of the input fields. `message`
        is the actual error message to be returned in the response.

        As a result of this method, the `errors` list is updated with an Error
        object to be returned as mutation result.
        """
        field = snake_to_camel_case(field)
        errors.append(Error(field=field, message=message))

    @classmethod
    def get_node_or_error(cls, info, global_id, errors, field, only_type=None):
        node = None
        try:
            node = graphene.Node.get_node_from_global_id(
                info, global_id, only_type)
        except (AssertionError, GraphQLError) as e:
            cls.add_error(errors, field, str(e))
        else:
            if node is None:
                message = "Couldn't resolve to a node: %s" % global_id
                cls.add_error(errors, field, message)
        return node

    @classmethod
    def get_nodes_or_error(cls, ids, errors, field, only_type=None):
        instances = None
        try:
            instances = get_nodes(ids, only_type)
        except GraphQLError as e:
            cls.add_error(field=field, message=str(e), errors=errors)
        return instances

    @classmethod
    def clean_instance(cls, instance, errors):
        """Clean the instance that was created using the input data.

        Once a instance is created, this method runs `full_clean()` to perform
        model fields' validation. Returns errors ready to be returned by
        the GraphQL response (if any occured).
        """
        try:
            instance.full_clean()
        except ValidationError as validation_errors:
            message_dict = validation_errors.message_dict
            for field in message_dict:
                if field in cls._meta.exclude:
                    continue
                for message in message_dict[field]:
                    field = snake_to_camel_case(field)
                    cls.add_error(errors, field, message)
        return errors


class ModelMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
            cls, arguments=None, model=None, exclude=None, _meta=None,
            **options):
        if not model:
            raise ImproperlyConfigured('model is required for ModelMutation')
        if not _meta:
            _meta = ModelMutationOptions(cls)

        if exclude is None:
            exclude = []

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
    def clean_input(cls, info, instance, input, errors):
        """Clean input data received from mutation arguments.

        Fields containing IDs or lists of IDs are automatically resolved into
        model instances. `instance` argument is the model instance the mutation
        is operating on (befor setting the input data). `input` is raw input
        data the mutation receives. `errors` is a list of errors that occurred
        during mutation's execution.

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
                        value, errors=errors,
                        field=field_name) if value else []
                    cleaned_input[field_name] = instances

                # handle ID field
                elif value is not None and is_id_field(field):
                    instance = cls.get_node_or_error(
                        info, value, errors=errors, field=field_name)
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
            if not f.editable or isinstance(
                    f, models.AutoField) or f.name not in cleaned_data:
                continue
            else:
                f.save_form_data(instance, cleaned_data[f.name])
        return instance

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        opts = instance._meta
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, 'save_form_data'):
                continue
            if f.name in cleaned_data and cleaned_data[f.name] is not None:
                f.save_form_data(instance, cleaned_data[f.name])

    @classmethod
    def user_is_allowed(cls, user, input):
        """Determine wheter user has rights to perform this mutation.

        Default implementation assumes that user is allowed to perform any
        mutation. By overriding this method, you can restrict access to it.
        `user` is the User instance associated with the request and `input` is
        the input data provided as mutation arguments.
        """
        return True

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(**{cls._meta.return_field_name: instance, 'errors': []})

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

    @classmethod
    def mutate(cls, root, info, **data):
        """Perform model mutation.

        Depending on the input data, `mutate` either creates a new instance or
        updates an existing one. If `id` arugment is present, it is assumed
        that this is an "update" mutation. Otherwise, a new instance is
        created based on the model associated with this mutation.
        """
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        id = data.get('id')
        input = data.get('input')

        # Initialize the errors list.
        errors = []

        # Initialize model instance based on presence of `id` attribute.
        if id:
            model_type = registry.get_type_for_model(cls._meta.model)
            instance = cls.get_node_or_error(
                info, id, errors, 'id', model_type)
        else:
            instance = cls._meta.model()
        if errors:
            return cls(errors=errors)

        cleaned_input = cls.clean_input(info, instance, input, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        if errors:
            return cls(errors=errors)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        return cls.success_response(instance)


class ModelDeleteMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, **data):
        """Perform a mutation that deletes a model instance."""
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        errors = []
        node_id = data.get('id')
        model_type = registry.get_type_for_model(cls._meta.model)
        instance = cls.get_node_or_error(
            info, node_id, errors, 'id', model_type)

        if errors:
            return cls(errors=errors)

        db_id = instance.id
        instance.delete()

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        return cls.success_response(instance)


class CreateToken(ObtainJSONWebToken):
    """Mutation that authenticates a user and returns token and user data.

    It overrides the default graphql_jwt.ObtainJSONWebToken to wrap potential
    authentication errors in our Error type, which is consistent to how rest of
    the mutation works.
    """

    errors = graphene.List(Error)
    user = graphene.Field(User)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            result = super().mutate(root, info, **kwargs)
        except GraphQLJWTError as e:
            return CreateToken(errors=[Error(message=str(e))])
        else:
            return result

    @classmethod
    def resolve(cls, root, info):
        return cls(user=info.context.user)


class VerifyToken(Verify):
    """Mutation that confirm if token is valid and also return user data."""

    user = graphene.Field(User)

    def resolve_user(self, info, **kwargs):
        email = self.payload.get('email')
        return models.User.objects.get(email=email)
