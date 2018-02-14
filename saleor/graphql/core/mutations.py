from collections import OrderedDict
from itertools import chain

import graphene
from django.core.exceptions import ImproperlyConfigured
from graphene.types.mutation import MutationOptions
from graphene_django.form_converter import convert_form_field
from graphene_django.registry import get_global_registry

from .types import ErrorType


def fields_for_form(form_class):
    fields = OrderedDict()
    for name, field in form_class.base_fields.items():
        fields[name] = convert_form_field(field)
    return fields


def convert_form_errors(form):
    """Convert ModelForm errors into a list of ErrorType objects."""
    errors = []
    for field in form.errors:
        for message in form.errors[field]:
            errors.append(ErrorType(field=field, message=message))
    return errors


class BaseMutation(graphene.Mutation):
    errors = graphene.List(ErrorType)

    class Meta:
        abstract = True


class ModelFormMutationOptions(MutationOptions):
    form_class = None
    return_field_name = None


class ModelFormMutation(BaseMutation):

    @classmethod
    def __init_subclass_with_meta__(
            cls, arguments=None, form_class=None, return_field_name=None,
            _meta=None, **options):
        if not form_class:
            raise ImproperlyConfigured(
                'form_class are required for ModelMutation')

        _meta = ModelFormMutationOptions(cls)
        model = form_class._meta.model
        registry = get_global_registry()
        model_type = registry.get_type_for_model(model)
        if not return_field_name:
            model_name = model.__name__
            return_field_name = model_name[:1].lower() + model_name[1:]

        # get mutation arguments based on model form
        arguments = fields_for_form(form_class)
        arguments['pk'] = graphene.Int()

        # get mutation output field for model instance
        fields = {return_field_name: graphene.Field(model_type)}

        _meta.form_class = form_class
        _meta.model = model
        _meta.return_field_name = return_field_name

        super(ModelFormMutation, cls).__init_subclass_with_meta__(
            _meta=_meta, **options)

        # Update mutation's arguments and fields
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = {'data': input}
        pk = input.pop('pk', None)
        if pk:
            instance = cls._meta.model._default_manager.get(pk=pk)
            kwargs['instance'] = instance
        return kwargs

    @classmethod
    def get_form(cls, root, info, **kwargs):
        form_kwargs = cls.get_form_kwargs(root, info, **kwargs)
        return cls._meta.form_class(**form_kwargs)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        form = cls.get_form(root, info, **kwargs)
        if form.is_valid():
            instance = form.save()
            kwargs = {cls._meta.return_field_name: instance}
            return cls(errors=[], **kwargs)
        else:
            errors = convert_form_errors(form)
            return cls(errors=errors)
