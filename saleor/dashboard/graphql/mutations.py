from collections import OrderedDict
from itertools import chain

import graphene
from django.core.exceptions import ImproperlyConfigured
from graphene.types.mutation import MutationOptions
from graphene_django.form_converter import convert_form_field
from graphene_django.registry import get_global_registry

from ...graphql.core.types import Error
from ...graphql.utils import get_node

registry = get_global_registry()


def convert_form_fields(form_class):
    """Convert form fields to Graphene fields"""
    fields = OrderedDict()
    for name, field in form_class.base_fields.items():
        fields[name] = convert_form_field(field)
    return fields


def convert_form_errors(form):
    """Convert ModelForm errors into a list of Error objects."""
    errors = []
    for field in form.errors:
        for message in form.errors[field]:
            errors.append(Error(field=field, message=message))
    return errors


class BaseMutation(graphene.Mutation):
    errors = graphene.List(Error)

    class Meta:
        abstract = True


class ModelFormMutationOptions(MutationOptions):
    form_class = None
    return_field_name = None


class ModelFormMutation(BaseMutation):

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
            cls, arguments=None, form_class=None, return_field_name=None,
            _meta=None, **options):
        if not form_class:
            raise ImproperlyConfigured(
                'form_class are required for ModelFormMutation')

        _meta = ModelFormMutationOptions(cls)
        model = form_class._meta.model
        model_type = registry.get_type_for_model(model)
        if not return_field_name:
            model_name = model.__name__
            return_field_name = model_name[:1].lower() + model_name[1:]

        # get mutation arguments based on model form
        arguments = convert_form_fields(form_class)

        # get mutation output field for model instance
        fields = {return_field_name: graphene.Field(model_type)}

        _meta.form_class = form_class
        _meta.model = model
        _meta.return_field_name = return_field_name

        super().__init_subclass_with_meta__(_meta=_meta, **options)

        # Update mutation's arguments and fields
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        return {'data': input}

    @classmethod
    def mutate(cls, root, info, **kwargs):
        form_kwargs = cls.get_form_kwargs(root, info, **kwargs)
        form = cls._meta.form_class(**form_kwargs)
        if form.is_valid():
            instance = form.save()
            kwargs = {cls._meta.return_field_name: instance}
            return cls(errors=[], **kwargs)
        else:
            errors = convert_form_errors(form)
            return cls(errors=errors)


class ModelFormUpdateMutation(ModelFormMutation):

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        super().__init_subclass_with_meta__(cls, *args, **kwargs)
        cls._meta.arguments.update({'id': graphene.ID()})

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        id = input['id']
        model = cls._meta.form_class._meta.model
        model_type = registry.get_type_for_model(model)
        instance = get_node(info, id, only_type=model_type)
        kwargs['instance'] = instance
        return kwargs
