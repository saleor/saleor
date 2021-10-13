from functools import singledispatch

from django import forms
from django.core.exceptions import ImproperlyConfigured

from graphene import ID, Boolean, Float, Int, List, String, UUID, Date, DateTime, Time

from .global_id_field import GlobalIDFormField, GlobalIDMultipleChoiceField


def get_form_field_description(field):
    return str(field.help_text) if field.help_text else None


@singledispatch
def convert_form_field(field):
    raise ImproperlyConfigured(
        "Don't know how to convert the Django form field %s (%s) "
        "to Graphene type" % (field, field.__class__)
    )


@convert_form_field.register(forms.fields.BaseTemporalField)
@convert_form_field.register(forms.CharField)
@convert_form_field.register(forms.EmailField)
@convert_form_field.register(forms.SlugField)
@convert_form_field.register(forms.URLField)
@convert_form_field.register(forms.ChoiceField)
@convert_form_field.register(forms.RegexField)
@convert_form_field.register(forms.Field)
def convert_form_field_to_string(field):
    return String(
        description=get_form_field_description(field), required=field.required
    )


@convert_form_field.register(forms.UUIDField)
def convert_form_field_to_uuid(field):
    return UUID(description=get_form_field_description(field), required=field.required)


@convert_form_field.register(forms.IntegerField)
@convert_form_field.register(forms.NumberInput)
def convert_form_field_to_int(field):
    return Int(description=get_form_field_description(field), required=field.required)


@convert_form_field.register(forms.BooleanField)
def convert_form_field_to_boolean(field):
    return Boolean(
        description=get_form_field_description(field), required=field.required
    )


@convert_form_field.register(forms.NullBooleanField)
def convert_form_field_to_nullboolean(field):
    return Boolean(description=get_form_field_description(field))


@convert_form_field.register(forms.DecimalField)
@convert_form_field.register(forms.FloatField)
def convert_form_field_to_float(field):
    return Float(description=get_form_field_description(field), required=field.required)


@convert_form_field.register(forms.MultipleChoiceField)
def convert_form_field_to_string_list(field):
    return List(
        String, description=get_form_field_description(field), required=field.required
    )


@convert_form_field.register(forms.ModelMultipleChoiceField)
@convert_form_field.register(GlobalIDMultipleChoiceField)
def convert_form_field_to_id_list(field):
    return List(ID, required=field.required)


@convert_form_field.register(forms.DateField)
def convert_form_field_to_date(field):
    return Date(description=get_form_field_description(field), required=field.required)


@convert_form_field.register(forms.DateTimeField)
def convert_form_field_to_datetime(field):
    return DateTime(
        description=get_form_field_description(field), required=field.required
    )


@convert_form_field.register(forms.TimeField)
def convert_form_field_to_time(field):
    return Time(description=get_form_field_description(field), required=field.required)


@convert_form_field.register(forms.ModelChoiceField)
@convert_form_field.register(GlobalIDFormField)
def convert_form_field_to_id(field):
    return ID(required=field.required)
