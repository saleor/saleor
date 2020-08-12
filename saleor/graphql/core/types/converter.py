import graphene
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField, TaxedMoneyField
from graphene_django.converter import convert_django_field
from graphene_django.forms.converter import convert_form_field

from ....account.models import PossiblePhoneNumberField
from ..filters import EnumFilter, ListObjectTypeFilter, ObjectTypeFilter
from .common import Weight
from .money import Money, TaxedMoney


@convert_django_field.register(PossiblePhoneNumberField)
def convert_phone_number_field_to_string(*_args):
    return graphene.String()


@convert_django_field.register(TaxedMoneyField)
def convert_field_taxed_money(*_args):
    return graphene.Field(TaxedMoney)


@convert_django_field.register(MoneyField)
def convert_field_money(*_args):
    return graphene.Field(Money)


@convert_django_field.register(MeasurementField)
def convert_field_measurements(*_args):
    return graphene.Field(Weight)


@convert_form_field.register(ObjectTypeFilter)
@convert_form_field.register(EnumFilter)
def convert_convert_enum(field):
    return field.input_class()


@convert_form_field.register(ListObjectTypeFilter)
def convert_list_object_type(field):
    return graphene.List(field.input_class)
