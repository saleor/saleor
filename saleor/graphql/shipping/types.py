import decimal

import graphene
from graphene import relay
from graphene.types import Scalar
from graphene_django import DjangoObjectType
from measurement.measures import Weight

from ...core.weight import convert_weight, get_default_weight_unit
from ...shipping import ShippingMethodType, models
from ..core.types.common import CountableDjangoObjectType
from ..core.types.money import MoneyRange


class ShippingZone(CountableDjangoObjectType):
    price_range = graphene.Field(
        MoneyRange, description="Lowest and highest prices for the shipping.")
    countries = graphene.List(
        graphene.String,
        description="List of countries available for the method.")

    class Meta:
        description = 'Represents a shipping zone in the shop.'
        model = models.ShippingZone
        interfaces = [relay.Node]
        filter_fields = {
            'name': ['icontains'],
            'countries': ['icontains'],
            'shipping_methods__price': ['gte', 'lte']}

    def resolve_price_range(self, info):
        return self.price_range

    def resolve_countries(self, info):
        return self.countries


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


class ShippingMethod(DjangoObjectType):

    class Meta:
        description = 'Shipping method within a shipping zone.'
        model = models.ShippingMethod
        interfaces = [relay.Node]
        exclude_fields = ['shipping_zone', 'orders']


class ShippingMethodTypeEnum(graphene.Enum):
    PRICE_BASED = ShippingMethodType.PRICE_BASED
    WEIGHT_BASED = ShippingMethodType.WEIGHT_BASED
