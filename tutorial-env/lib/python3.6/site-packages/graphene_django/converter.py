from django.db import models
from django.utils.encoding import force_text

from graphene import (
    ID,
    Boolean,
    Dynamic,
    Enum,
    Field,
    Float,
    Int,
    List,
    NonNull,
    String,
    UUID,
    DateTime,
    Date,
    Time,
)
from graphene.types.json import JSONString
from graphene.utils.str_converters import to_camel_case, to_const
from graphql import assert_valid_name

from .compat import ArrayField, HStoreField, JSONField, RangeField
from .fields import DjangoListField, DjangoConnectionField
from .utils import import_single_dispatch

singledispatch = import_single_dispatch()


def convert_choice_name(name):
    name = to_const(force_text(name))
    try:
        assert_valid_name(name)
    except AssertionError:
        name = "A_%s" % name
    return name


def get_choices(choices):
    converted_names = []
    for value, help_text in choices:
        if isinstance(help_text, (tuple, list)):
            for choice in get_choices(help_text):
                yield choice
        else:
            name = convert_choice_name(value)
            while name in converted_names:
                name += "_" + str(len(converted_names))
            converted_names.append(name)
            description = help_text
            yield name, value, description


def convert_django_field_with_choices(field, registry=None):
    if registry is not None:
        converted = registry.get_converted_field(field)
        if converted:
            return converted
    choices = getattr(field, "choices", None)
    if choices:
        meta = field.model._meta
        name = to_camel_case("{}_{}".format(meta.object_name, field.name))
        choices = list(get_choices(choices))
        named_choices = [(c[0], c[1]) for c in choices]
        named_choices_descriptions = {c[0]: c[2] for c in choices}

        class EnumWithDescriptionsType(object):
            @property
            def description(self):
                return named_choices_descriptions[self.name]

        enum = Enum(name, list(named_choices), type=EnumWithDescriptionsType)
        converted = enum(description=field.help_text, required=not field.null)
    else:
        converted = convert_django_field(field, registry)
    if registry is not None:
        registry.register_converted_field(field, converted)
    return converted


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
    return String(description=field.help_text, required=not field.null)


@convert_django_field.register(models.AutoField)
def convert_field_to_id(field, registry=None):
    return ID(description=field.help_text, required=not field.null)


@convert_django_field.register(models.UUIDField)
def convert_field_to_uuid(field, registry=None):
    return UUID(description=field.help_text, required=not field.null)


@convert_django_field.register(models.PositiveIntegerField)
@convert_django_field.register(models.PositiveSmallIntegerField)
@convert_django_field.register(models.SmallIntegerField)
@convert_django_field.register(models.BigIntegerField)
@convert_django_field.register(models.IntegerField)
def convert_field_to_int(field, registry=None):
    return Int(description=field.help_text, required=not field.null)


@convert_django_field.register(models.BooleanField)
def convert_field_to_boolean(field, registry=None):
    return NonNull(Boolean, description=field.help_text)


@convert_django_field.register(models.NullBooleanField)
def convert_field_to_nullboolean(field, registry=None):
    return Boolean(description=field.help_text, required=not field.null)


@convert_django_field.register(models.DecimalField)
@convert_django_field.register(models.FloatField)
@convert_django_field.register(models.DurationField)
def convert_field_to_float(field, registry=None):
    return Float(description=field.help_text, required=not field.null)


@convert_django_field.register(models.DateTimeField)
def convert_datetime_to_string(field, registry=None):
    return DateTime(description=field.help_text, required=not field.null)


@convert_django_field.register(models.DateField)
def convert_date_to_string(field, registry=None):
    return Date(description=field.help_text, required=not field.null)


@convert_django_field.register(models.TimeField)
def convert_time_to_string(field, registry=None):
    return Time(description=field.help_text, required=not field.null)


@convert_django_field.register(models.OneToOneRel)
def convert_onetoone_field_to_djangomodel(field, registry=None):
    model = field.related_model

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        # We do this for a bug in Django 1.8, where null attr
        # is not available in the OneToOneRel instance
        null = getattr(field, "null", True)
        return Field(_type, required=not null)

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

        # If there is a connection, we should transform the field
        # into a DjangoConnectionField
        if _type._meta.connection:
            # Use a DjangoFilterConnectionField if there are
            # defined filter_fields in the DjangoObjectType Meta
            if _type._meta.filter_fields:
                from .filter.fields import DjangoFilterConnectionField

                return DjangoFilterConnectionField(_type)

            return DjangoConnectionField(_type)

        return DjangoListField(_type)

    return Dynamic(dynamic_type)


@convert_django_field.register(models.OneToOneField)
@convert_django_field.register(models.ForeignKey)
def convert_field_to_djangomodel(field, registry=None):
    model = field.related_model

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        return Field(_type, description=field.help_text, required=not field.null)

    return Dynamic(dynamic_type)


@convert_django_field.register(ArrayField)
def convert_postgres_array_to_list(field, registry=None):
    base_type = convert_django_field(field.base_field)
    if not isinstance(base_type, (List, NonNull)):
        base_type = type(base_type)
    return List(base_type, description=field.help_text, required=not field.null)


@convert_django_field.register(HStoreField)
@convert_django_field.register(JSONField)
def convert_posgres_field_to_string(field, registry=None):
    return JSONString(description=field.help_text, required=not field.null)


@convert_django_field.register(RangeField)
def convert_posgres_range_to_string(field, registry=None):
    inner_type = convert_django_field(field.base_field)
    if not isinstance(inner_type, (List, NonNull)):
        inner_type = type(inner_type)
    return List(inner_type, description=field.help_text, required=not field.null)
