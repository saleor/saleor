from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers

import graphene

from ..registry import get_global_registry
from ..utils import import_single_dispatch
from .types import DictType

singledispatch = import_single_dispatch()


@singledispatch
def get_graphene_type_from_serializer_field(field):
    raise ImproperlyConfigured(
        "Don't know how to convert the serializer field %s (%s) "
        "to Graphene type" % (field, field.__class__)
    )


def convert_serializer_field(field, is_input=True):
    """
    Converts a django rest frameworks field to a graphql field
    and marks the field as required if we are creating an input type
    and the field itself is required
    """

    graphql_type = get_graphene_type_from_serializer_field(field)

    args = []
    kwargs = {"description": field.help_text, "required": is_input and field.required}

    # if it is a tuple or a list it means that we are returning
    # the graphql type and the child type
    if isinstance(graphql_type, (list, tuple)):
        kwargs["of_type"] = graphql_type[1]
        graphql_type = graphql_type[0]

    if isinstance(field, serializers.ModelSerializer):
        if is_input:
            graphql_type = convert_serializer_to_input_type(field.__class__)
        else:
            global_registry = get_global_registry()
            field_model = field.Meta.model
            args = [global_registry.get_type_for_model(field_model)]
    elif isinstance(field, serializers.ListSerializer):
        field = field.child
        if is_input:
            kwargs["of_type"] = convert_serializer_to_input_type(field.__class__)
        else:
            del kwargs["of_type"]
            global_registry = get_global_registry()
            field_model = field.Meta.model
            args = [global_registry.get_type_for_model(field_model)]

    return graphql_type(*args, **kwargs)


def convert_serializer_to_input_type(serializer_class):
    serializer = serializer_class()

    items = {
        name: convert_serializer_field(field)
        for name, field in serializer.fields.items()
    }

    return type(
        "{}Input".format(serializer.__class__.__name__),
        (graphene.InputObjectType,),
        items,
    )


@get_graphene_type_from_serializer_field.register(serializers.Field)
def convert_serializer_field_to_string(field):
    return graphene.String


@get_graphene_type_from_serializer_field.register(serializers.ModelSerializer)
def convert_serializer_to_field(field):
    return graphene.Field


@get_graphene_type_from_serializer_field.register(serializers.ListSerializer)
def convert_list_serializer_to_field(field):
    child_type = get_graphene_type_from_serializer_field(field.child)
    return (graphene.List, child_type)


@get_graphene_type_from_serializer_field.register(serializers.IntegerField)
def convert_serializer_field_to_int(field):
    return graphene.Int


@get_graphene_type_from_serializer_field.register(serializers.BooleanField)
def convert_serializer_field_to_bool(field):
    return graphene.Boolean


@get_graphene_type_from_serializer_field.register(serializers.FloatField)
@get_graphene_type_from_serializer_field.register(serializers.DecimalField)
def convert_serializer_field_to_float(field):
    return graphene.Float


@get_graphene_type_from_serializer_field.register(serializers.DateTimeField)
def convert_serializer_field_to_datetime_time(field):
    return graphene.types.datetime.DateTime


@get_graphene_type_from_serializer_field.register(serializers.DateField)
def convert_serializer_field_to_date_time(field):
    return graphene.types.datetime.Date


@get_graphene_type_from_serializer_field.register(serializers.TimeField)
def convert_serializer_field_to_time(field):
    return graphene.types.datetime.Time


@get_graphene_type_from_serializer_field.register(serializers.ListField)
def convert_serializer_field_to_list(field, is_input=True):
    child_type = get_graphene_type_from_serializer_field(field.child)

    return (graphene.List, child_type)


@get_graphene_type_from_serializer_field.register(serializers.DictField)
def convert_serializer_field_to_dict(field):
    return DictType


@get_graphene_type_from_serializer_field.register(serializers.JSONField)
def convert_serializer_field_to_jsonstring(field):
    return graphene.types.json.JSONString


@get_graphene_type_from_serializer_field.register(serializers.MultipleChoiceField)
def convert_serializer_field_to_list_of_string(field):
    return (graphene.List, graphene.String)
