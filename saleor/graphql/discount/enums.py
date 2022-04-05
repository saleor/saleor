import graphene

from ...discount import DiscountType, DiscountValueType, VoucherType
from ..core.enums import to_enum

DiscountTypeEnum = to_enum(DiscountType, type_name="DiscountType")


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
