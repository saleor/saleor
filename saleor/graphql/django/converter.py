from collections import OrderedDict
from functools import singledispatch, wraps

from django.db import models
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.utils.module_loading import import_string

from graphene import (
    ID,
    UUID,
    Boolean,
    Date,
    DateTime,
    Dynamic,
    Enum,
    Field,
    Float,
    Int,
    List,
    NonNull,
    String,
    Time,
    Decimal,
)
from graphene.types.json import JSONString
from graphene.utils.str_converters import to_camel_case
from graphql import GraphQLError, assert_valid_name
from graphql.pyutils import register_description

from .compat import ArrayField, HStoreField, JSONField, PGJSONField, RangeField
from .fields import DjangoListField, DjangoConnectionField
from .settings import graphene_settings
from .utils.str_converters import to_const


class BlankValueField(Field):
    def wrap_resolve(self, parent_resolver):
        resolver = self.resolver or parent_resolver

        # create custom resolver
        def blank_field_wrapper(func):
            @wraps(func)
            def wrapped_resolver(*args, **kwargs):
                return_value = func(*args, **kwargs)
                if return_value == "":
                    return None
                return return_value

            return wrapped_resolver

        return blank_field_wrapper(resolver)


def convert_choice_name(name):
    name = to_const(force_str(name))
    try:
        assert_valid_name(name)
    except GraphQLError:
        name = "A_%s" % name
    return name


def get_choices(choices):
    converted_names = []
    if isinstance(choices, OrderedDict):
        choices = choices.items()
    for value, help_text in choices:
        if isinstance(help_text, (tuple, list)):
            for choice in get_choices(help_text):
                yield choice
        else:
            name = convert_choice_name(value)
            while name in converted_names:
                name += "_" + str(len(converted_names))
            converted_names.append(name)
            description = str(
                help_text
            )  # TODO: translatable description: https://github.com/graphql-python/graphql-core-next/issues/58
            yield name, value, description


def convert_choices_to_named_enum_with_descriptions(name, choices):
    choices = list(get_choices(choices))
    named_choices = [(c[0], c[1]) for c in choices]
    named_choices_descriptions = {c[0]: c[2] for c in choices}

    class EnumWithDescriptionsType(object):
        @property
        def description(self):
            return str(named_choices_descriptions[self.name])

    return_type = Enum(name, list(named_choices), type=EnumWithDescriptionsType)
    return return_type


def generate_enum_name(django_model_meta, field):
    if graphene_settings.DJANGO_CHOICE_FIELD_ENUM_CUSTOM_NAME:
        # Try and import custom function
        custom_func = import_string(
            graphene_settings.DJANGO_CHOICE_FIELD_ENUM_CUSTOM_NAME
        )
        name = custom_func(field)
    elif graphene_settings.DJANGO_CHOICE_FIELD_ENUM_V2_NAMING is True:
        name = to_camel_case("{}_{}".format(django_model_meta.object_name, field.name))
    else:
        name = "{app_label}{object_name}{field_name}Choices".format(
            app_label=to_camel_case(django_model_meta.app_label.title()),
            object_name=django_model_meta.object_name,
            field_name=to_camel_case(field.name.title()),
        )
    return name


def convert_choice_field_to_enum(field, name=None):
    if name is None:
        name = generate_enum_name(field.model._meta, field)
    choices = field.choices
    return convert_choices_to_named_enum_with_descriptions(name, choices)


def convert_django_field_with_choices(
    field, registry=None, convert_choices_to_enum=True
):
    if registry is not None:
        converted = registry.get_converted_field(field)
        if converted:
            return converted
    choices = getattr(field, "choices", None)
    if choices and convert_choices_to_enum:
        EnumCls = convert_choice_field_to_enum(field)
        required = not (field.blank or field.null)

        converted = EnumCls(
            description=get_django_field_description(field), required=required
        ).mount_as(BlankValueField)
    else:
        converted = convert_django_field(field, registry)
    if registry is not None:
        registry.register_converted_field(field, converted)
    return converted


def get_django_field_description(field):
    return str(field.help_text) if field.help_text else None


@singledispatch
def convert_django_field(field, registry=None):
    raise Exception(
        "Don't know how to convert the Django field %s (%s)" % (field, field.__class__)
    )


@convert_django_field.register(models.CharField)
@convert_django_field.register(models.TextField)
@convert_django_field.register(models.EmailField)
@convert_django_field.register(models.SlugField)
@convert_django_field.register(models.URLField)
@convert_django_field.register(models.GenericIPAddressField)
@convert_django_field.register(models.FileField)
@convert_django_field.register(models.FilePathField)
def convert_field_to_string(field, registry=None):
    return String(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(models.BigAutoField)
@convert_django_field.register(models.AutoField)
def convert_field_to_id(field, registry=None):
    return ID(description=get_django_field_description(field), required=not field.null)


if hasattr(models, "SmallAutoField"):

    @convert_django_field.register(models.SmallAutoField)
    def convert_field_small_to_id(field, registry=None):
        return convert_field_to_id(field, registry)


@convert_django_field.register(models.UUIDField)
def convert_field_to_uuid(field, registry=None):
    return UUID(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(models.PositiveIntegerField)
@convert_django_field.register(models.PositiveSmallIntegerField)
@convert_django_field.register(models.SmallIntegerField)
@convert_django_field.register(models.BigIntegerField)
@convert_django_field.register(models.IntegerField)
def convert_field_to_int(field, registry=None):
    return Int(description=get_django_field_description(field), required=not field.null)


@convert_django_field.register(models.NullBooleanField)
@convert_django_field.register(models.BooleanField)
def convert_field_to_boolean(field, registry=None):
    return Boolean(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(models.DecimalField)
def convert_field_to_decimal(field, registry=None):
    return Decimal(description=field.help_text, required=not field.null)


@convert_django_field.register(models.FloatField)
@convert_django_field.register(models.DurationField)
def convert_field_to_float(field, registry=None):
    return Float(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(models.DateTimeField)
def convert_datetime_to_string(field, registry=None):
    return DateTime(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(models.DateField)
def convert_date_to_string(field, registry=None):
    return Date(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(models.TimeField)
def convert_time_to_string(field, registry=None):
    return Time(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(models.OneToOneRel)
def convert_onetoone_field_to_djangomodel(field, registry=None):
    model = field.related_model

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        return Field(_type, required=not field.null)

    return Dynamic(dynamic_type)


@convert_django_field.register(models.ManyToManyField)
@convert_django_field.register(models.ManyToManyRel)
@convert_django_field.register(models.ManyToOneRel)
def convert_field_to_list_or_connection(field, registry=None):
    model = field.related_model

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        if isinstance(field, models.ManyToManyField):
            description = get_django_field_description(field)
        else:
            description = get_django_field_description(field.field)

        # If there is a connection, we should transform the field
        # into a DjangoConnectionField
        if _type._meta.connection:
            # Use a DjangoFilterConnectionField if there are
            # defined filter_fields or a filterset_class in the
            # DjangoObjectType Meta
            if _type._meta.filter_fields or _type._meta.filterset_class:
                from .filter.fields import DjangoFilterConnectionField

                return DjangoFilterConnectionField(
                    _type, required=True, description=description
                )

            return DjangoConnectionField(_type, required=True, description=description)

        return DjangoListField(
            _type,
            required=True,  # A Set is always returned, never None.
            description=description,
        )

    return Dynamic(dynamic_type)


@convert_django_field.register(models.OneToOneField)
@convert_django_field.register(models.ForeignKey)
def convert_field_to_djangomodel(field, registry=None):
    model = field.related_model

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        return Field(
            _type,
            description=get_django_field_description(field),
            required=not field.null,
        )

    return Dynamic(dynamic_type)


@convert_django_field.register(ArrayField)
def convert_postgres_array_to_list(field, registry=None):
    inner_type = convert_django_field(field.base_field)
    if not isinstance(inner_type, (List, NonNull)):
        inner_type = (
            NonNull(type(inner_type))
            if inner_type.kwargs["required"]
            else type(inner_type)
        )
    return List(
        inner_type,
        description=get_django_field_description(field),
        required=not field.null,
    )


@convert_django_field.register(HStoreField)
@convert_django_field.register(PGJSONField)
@convert_django_field.register(JSONField)
def convert_pg_and_json_field_to_string(field, registry=None):
    return JSONString(
        description=get_django_field_description(field), required=not field.null
    )


@convert_django_field.register(RangeField)
def convert_postgres_range_to_string(field, registry=None):
    inner_type = convert_django_field(field.base_field)
    if not isinstance(inner_type, (List, NonNull)):
        inner_type = (
            NonNull(type(inner_type))
            if inner_type.kwargs["required"]
            else type(inner_type)
        )
    return List(
        inner_type,
        description=get_django_field_description(field),
        required=not field.null,
    )


# Register Django lazy()-wrapped values as GraphQL description/help_text.
# This is needed for using lazy translations, see https://github.com/graphql-python/graphql-core-next/issues/58.
register_description(Promise)
