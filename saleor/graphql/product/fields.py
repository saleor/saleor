import graphene
from django import forms
from graphene_django.form_converter import convert_form_field

from .scalars import AttributeScalar


class AttributeField(forms.Field):
    pass


@convert_form_field.register(AttributeField)
def convert_form_field_to_list(field):
    return graphene.List(AttributeScalar)
