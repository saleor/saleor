from itertools import chain

import graphene
from django.core.exceptions import ImproperlyConfigured, ValidationError
from graphene.types.mutation import MutationOptions
from graphene_django.registry import get_global_registry
from graphene_file_upload import Upload
from graphql_jwt import ObtainJSONWebToken, Verify
from graphql_jwt.exceptions import GraphQLJWTError, PermissionDenied

from ...account import models
from ..account.types import User
from ..utils import get_node, get_nodes
from .types import Error

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
    model = None


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


class ModelMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
            cls, arguments=None, model=None, permissions=None, _meta=None,
            **options):
        if not model:
            raise ImproperlyConfigured('model is required for ModelMutation')
        _meta = ModelMutationOptions(cls)
        return_field_name = get_model_name(model)
        if arguments is None:
            arguments = {}
        fields = get_output_fields(model, return_field_name)
        _meta.model = model
        _meta.return_field_name = return_field_name
        super().__init_subclass_with_meta__(_meta=_meta, **options)
        cls._update_mutation_arguments_and_fields(
            arguments=arguments, fields=fields)

    @classmethod
    def add_error(cls, errors, field, message):
        errors.append(Error(field=field, message=message))
        return errors

    @classmethod
    def _check_type(cls, field, target_type):
        if hasattr(field.type, 'of_type'):
            return field.type.of_type == target_type
        return field.type == target_type

    @classmethod
    def _clean_input(cls, info, instance, input, errors):
        InputCls = getattr(cls.Arguments, 'input')
        cleaned_input = {}
        for field_name, field in InputCls._meta.fields.items():
            if field_name in input:
                value = input[field_name]
                if value is not None:
                    # FIXME: maybe we could have custom input field type that takes
                    # the type of IDs e.g. graphene.IdList(graphene.ID, type=Product).

                    # handle list of IDs field
                    if isinstance(field.type, graphene.List) and field.type.of_type == graphene.ID:
                        instances = get_nodes(value) if value else []
                        cleaned_input[field_name] = instances

                    # handle ID field
                    elif field.type == graphene.ID:
                        instance = get_node(info, value)
                        cleaned_input[field_name] = instance

                    # handle uploaded files
                    elif cls._check_type(field, Upload):
                        value = info.context.FILES.get(value)
                        cleaned_input[field_name] = value

                    # handle other fields
                    else:
                        cleaned_input[field_name] = value
        return cleaned_input, errors

    @classmethod
    def _construct_instance(cls, instance, cleaned_data):
        """
        Construct and return a model instance from ``cleaned_data``, but do
        not save the returned instance to the database.
        """
        from django.db import models
        opts = instance._meta

        for f in opts.fields:
            if not f.editable or isinstance(f, models.AutoField) or f.name not in cleaned_data:
                continue
            if f.name in cleaned_data and cleaned_data[f.name] is None:
                continue
            else:
                f.save_form_data(instance, cleaned_data[f.name])

        return instance

    @classmethod
    def _clean_instance(cls, instance, errors):
        try:
            instance.full_clean()
        except ValidationError as validation_errors:
            message_dict = validation_errors.message_dict
            for field in message_dict:
                for message in message_dict[field]:
                    cls.add_error(errors, field, message)
        return errors

    @classmethod
    def _save_m2m(cls, instance, cleaned_data):
        opts = instance._meta
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, 'save_form_data'):
                continue
            if f.name in cleaned_data and cleaned_data[f.name] is not None:
                f.save_form_data(instance, cleaned_data[f.name])

    @classmethod
    def user_is_allowed(cls, user, input):
        return True

    @classmethod
    def success_response(cls, instance):
        return cls(**{cls._meta.return_field_name: instance}, errors=[])

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        id = data.get('id')
        input = data.get('input')

        errors = []

        # initialize model instance
        if id:
            model_type = registry.get_type_for_model(cls._meta.model)
            instance = get_node(info, id, only_type=model_type)
        else:
            instance = cls._meta.model()

        cleaned_input, errors = cls._clean_input(info, instance, input, errors)
        instance = cls._construct_instance(instance, cleaned_input)
        errors = cls._clean_instance(instance, errors)

        if errors:
            return cls(errors=errors)

        instance.save()
        cls._save_m2m(instance, cleaned_input)
        return cls.success_response(instance)


class ModelDeleteMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        id = data.get('id')
        model_type = registry.get_type_for_model(cls._meta.model)
        instance = get_node(info, id, only_type=model_type)
        instance.delete()
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
    """Mutation that confirm if token is valid and also return user data.

    """
    user = graphene.Field(User)

    def resolve_user(self, info, **kwargs):
        email = self.payload.get('email')
        return models.User.objects.get(email=email)
