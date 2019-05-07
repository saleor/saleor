import graphene
from graphene_django.converter import convert_django_field

from ...account.models import PossiblePhoneNumberField


@convert_django_field.register(PossiblePhoneNumberField)
def convert_json_field_to_string(*_args):
    return graphene.String()
