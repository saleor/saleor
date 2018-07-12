import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from ...shipping import models
from ..core.types import CountableDjangoObjectType, MoneyRange


class ShippingMethod(CountableDjangoObjectType):
    price_range = graphene.Field(
        MoneyRange, description="Lowest and highest prices for the shipping.")
    countries = graphene.List(
        graphene.String,
        description="List of countries available for the method.")

    class Meta:
        description = 'Represents a shipping method in the shop.'
        model = models.ShippingMethod
        interfaces = [relay.Node]
        filter_fields = {
            'name': ['icontains'],
            'description': ['icontains'],
            'price_per_country__price': ['gte', 'lte']
        }

    def resolve_price_range(self, info):
        return self.price_range

    def resolve_countries(self, info):
        return self.countries


class ShippingMethodCountry(DjangoObjectType):
    class Meta:
        description = 'Country to which shipping applies.'
        model = models.ShippingMethodCountry
        interfaces = [relay.Node]
        exclude_fields = ['shipping_method', 'orders']
