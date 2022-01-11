import graphene

from ...discount import DiscountValueType, OrderDiscountType, VoucherType
from ..core.enums import to_enum

OrderDiscountTypeEnum = to_enum(OrderDiscountType, type_name="OrderDiscountType")


class SaleType(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE


class DiscountValueTypeEnum(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE


class VoucherTypeEnum(graphene.Enum):
    SHIPPING = VoucherType.SHIPPING
    ENTIRE_ORDER = VoucherType.ENTIRE_ORDER
    SPECIFIC_PRODUCT = VoucherType.SPECIFIC_PRODUCT


class DiscountStatusEnum(graphene.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"


class VoucherDiscountType(graphene.Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    SHIPPING = "shipping"
