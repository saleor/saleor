from textwrap import dedent

import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from ...shipping import models
from ..core.connection import CountableDjangoObjectType
from ..core.types import CountryDisplay, MoneyRange
from .enums import ShippingMethodTypeEnum


class ShippingMethod(CountableDjangoObjectType):
    type = ShippingMethodTypeEnum(description='Type of the shipping method.')

    class Meta:
        description = dedent("""
            Shipping method are the methods you'll use to get
            customer's orders to them.
            They are directly exposed to the customers.""")
        model = models.ShippingMethod
        interfaces = [relay.Node]
        exclude_fields = ['carts', 'shipping_zone', 'orders']


class ShippingZone(CountableDjangoObjectType):
    price_range = graphene.Field(
        MoneyRange, description='Lowest and highest prices for the shipping.')
    countries = graphene.List(
        CountryDisplay,
        description='List of countries available for the method.')
    shipping_methods = gql_optimizer.field(
        graphene.List(
            ShippingMethod,
            description=(
                'List of shipping methods available for orders'
                ' shipped to countries within this shipping zone.')),
        model_field='shipping_methods')

    class Meta:
        description = dedent("""
            Represents a shipping zone in the shop. Zones are the concept
            used only for grouping shipping methods in the dashboard,
            and are never exposed to the customers directly.""")
        model = models.ShippingZone
        interfaces = [relay.Node]

    def resolve_price_range(self, info):
        return self.price_range

    def resolve_countries(self, info):
        return [
            CountryDisplay(code=country.code, country=country.name)
            for country in self.countries]

    def resolve_shipping_methods(self, info):
        return self.shipping_methods.all()
