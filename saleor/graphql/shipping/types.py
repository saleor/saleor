import decimal

import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay
from graphene.types import Scalar
from measurement.measures import Weight
from textwrap import dedent

from ...core.weight import convert_weight, get_default_weight_unit
from ...shipping import ShippingMethodType, models
from ..core.types.common import CountableDjangoObjectType, CountryDisplay
from ..core.types.money import MoneyRange

ShippingMethodTypeEnum = graphene.Enum(
    'ShippingMethodTypeEnum',
    [(code.upper(), code) for code, name in ShippingMethodType.CHOICES])


class ShippingMethod(CountableDjangoObjectType):
    type = ShippingMethodTypeEnum(description='Type of the shipping method.')

    class Meta:
        description = dedent("""
            Shipping method are the methods you'll use to get
            customer's orders to them.
            They are directly exposed to the customers.""")
        model = models.ShippingMethod
        interfaces = [relay.Node]
        exclude_fields = ['shipping_zone', 'orders']


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


class WeightScalar(Scalar):
    @staticmethod
    def parse_value(value):
        """Excepts value to be a string "amount unit"
        separated by a single space.
        """
        try:
            value = decimal.Decimal(value)
        except decimal.DecimalException:
            return None
        default_unit = get_default_weight_unit()
        return Weight(**{default_unit: value})

    @staticmethod
    def serialize(weight):
        if isinstance(weight, Weight):
            default_unit = get_default_weight_unit()
            if weight.unit != default_unit:
                weight = convert_weight(weight, default_unit)
            return str(weight)
        return None

    @staticmethod
    def parse_literal(node):
        return node
