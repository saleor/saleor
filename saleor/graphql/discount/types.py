import graphene
from graphene import relay

from ...discount import DiscountValueType, VoucherType, models
from ..core.types.common import CountableDjangoObjectType


class Voucher(CountableDjangoObjectType):
    class Meta:
        description = """A token that can be used to purchase products
        for discounted price."""
        interfaces = [relay.Node]
        model = models.Voucher


class Sale(CountableDjangoObjectType):
    class Meta:
        description = """A special event featuring discounts
        for selected products"""
        interfaces = [relay.Node]
        model = models.Sale


class VoucherTypeEnum(graphene.Enum):
    PRODUCT = VoucherType.PRODUCT
    COLLECTION = VoucherType.COLLECTION
    CATEGORY = VoucherType.CATEGORY
    SHIPPING = VoucherType.SHIPPING
    VALUE = VoucherType.VALUE


class DiscountValueTypeEnum(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE
