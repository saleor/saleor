from collections import OrderedDict

from django.shortcuts import get_object_or_404

import graphene
from graphene.types import Field, InputField
from graphene.types.mutation import MutationOptions
from graphene.relay.mutation import ClientIDMutation
from graphene.types.objecttype import yank_fields_from_attrs

from .serializer_converter import convert_serializer_field
from .types import ErrorType


class SerializerMutationOptions(MutationOptions):
    lookup_field = None
    model_class = None
    model_operations = ["create", "update"]
    serializer_class = None


def fields_for_serializer(serializer, only_fields, exclude_fields, is_input=False):
    fields = OrderedDict()
    for name, field in serializer.fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = (
            name
            in exclude_fields  # or
            # name in already_created_fields
        )

        if is_not_in_only or is_excluded:
            continue

        fields[name] = convert_serializer_field(field, is_input=is_input)
    return fields


class SerializerMutation(ClientIDMutation):
    class Meta:
        abstract = True

    errors = graphene.List(
        ErrorType, description="May contain more than one error for same field."
    )

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        lookup_field=None,
        serializer_class=None,
        model_class=None,
        model_operations=["create", "update"],
        only_fields=(),
        exclude_fields=(),
        **options
    ):

        if not serializer_class:
            raise Exception("serializer_class is required for the SerializerMutation")

        if "update" not in model_operations and "create" not in model_operations:
            raise Exception('model_operations must contain "create" and/or "update"')

        serializer = serializer_class()
        if model_class is None:
            serializer_meta = getattr(serializer_class, "Meta", None)
            if serializer_meta:
                model_class = getattr(serializer_meta, "model", None)

        if lookup_field is None and model_class:
            lookup_field = model_class._meta.pk.name

        input_fields = fields_for_serializer(
            serializer, only_fields, exclude_fields, is_input=True
        )
        output_fields = fields_for_serializer(
            serializer, only_fields, exclude_fields, is_input=False
        )

        _meta = SerializerMutationOptions(cls)
        _meta.lookup_field = lookup_field
        _meta.model_operations = model_operations
        _meta.serializer_class = serializer_class
        _meta.model_class = model_class
        _meta.fields = yank_fields_from_attrs(output_fields, _as=Field)

        input_fields = yank_fields_from_attrs(input_fields, _as=InputField)
        super(SerializerMutation, cls).__init_subclass_with_meta__(
            _meta=_meta, input_fields=input_fields, **options
        )

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        lookup_field = cls._meta.lookup_field
        model_class = cls._meta.model_class

        if model_class:
            if "update" in cls._meta.model_operations and lookup_field in input:
                instance = get_object_or_404(
                    model_class, **{lookup_field: input[lookup_field]}
                )
            elif "create" in cls._meta.model_operations:
                instance = None
            else:
                raise Exception(
                    'Invalid update operation. Input parameter "{}" required.'.format(
                        lookup_field
                    )
                )

            return {
                "instance": instance,
                "data": input,
                "context": {"request": info.context},
            }

        return {"data": input, "context": {"request": info.context}}

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        kwargs = cls.get_serializer_kwargs(root, info, **input)
        serializer = cls._meta.serializer_class(**kwargs)

        if serializer.is_valid():
            return cls.perform_mutate(serializer, info)
        else:
            errors = [
                ErrorType(field=key, messages=value)
                for key, value in serializer.errors.items()
            ]

            return cls(errors=errors)

    @classmethod
    def perform_mutate(cls, serializer, info):
        obj = serializer.save()

        kwargs = {}
        for f, field in serializer.fields.items():
            kwargs[f] = field.get_attribute(obj)

        return cls(errors=None, **kwargs)
