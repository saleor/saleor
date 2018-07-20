import graphene
from graphene import relay

from ...discount import (
    DiscountValueType, VoucherType, models)
from ..core.types.common import CountableDjangoObjectType


class Voucher(CountableDjangoObjectType):
    class Meta:
        description = """A token that can be used to purchase products
        for discounted price."""
        interfaces = [relay.Node]
        filter_fields = {
            'name': ['icontains'],
            'type': ['exact'],
            'discount_value': ['gte', 'lte'],
            'start_date': ['exact'],
            'end_date': ['exact'],
            'min_amount_spent': ['gte', 'lte']}
        model = models.Voucher


class Sale(CountableDjangoObjectType):
    class Meta:
        description = """A special event featuring discounts
        for selected products"""
        interfaces = [relay.Node]
        filter_fields = {
            'name': ['icontains'],
            'type': ['icontains'],
            'value': ['gte', 'lte']}
        model = models.Sale


class VoucherTypeEnum(graphene.Enum):
    PRODUCT = VoucherType.PRODUCT
    CATEGORY = VoucherType.CATEGORY
    SHIPPING = VoucherType.SHIPPING
    VALUE = VoucherType.VALUE


class DiscountValueTypeEnum(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE
