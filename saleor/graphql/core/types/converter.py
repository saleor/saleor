from graphene import List
from graphene_django.forms.converter import convert_form_field

from ..filters import EnumFilter, ListObjectTypeFilter, ObjectTypeFilter


@convert_form_field.register(ObjectTypeFilter)
@convert_form_field.register(EnumFilter)
def convert_convert_enum(field):
    return field.input_class()


@convert_form_field.register(ListObjectTypeFilter)
def convert_list_object_type(field):
    return List(field.input_class)
