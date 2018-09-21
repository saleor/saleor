import graphene
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField, TaxedMoneyField
from graphene_django.converter import convert_django_field
from graphene_django.fields import DjangoConnectionField

from .types.common import Weight
from .types.money import Money, TaxedMoney


@convert_django_field.register(TaxedMoneyField)
def convert_field_taxed_money(field, registry=None):
    return graphene.Field(TaxedMoney)


@convert_django_field.register(MoneyField)
def convert_field_money(field, registry=None):
    return graphene.Field(Money)


@convert_django_field.register(MeasurementField)
def convert_field_measurements(field, registry=None):
    return graphene.Field(Weight)


class PrefetchingConnectionField(DjangoConnectionField):

    @classmethod
    def merge_querysets(cls, default_queryset, queryset):
        return queryset
