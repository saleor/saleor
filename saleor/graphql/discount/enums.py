import graphene

from ...discount import DiscountValueType, VoucherType


class DiscountValueTypeEnum(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE


class VoucherTypeEnum(graphene.Enum):
    PRODUCT = VoucherType.PRODUCT
    COLLECTION = VoucherType.COLLECTION
    CATEGORY = VoucherType.CATEGORY
    SHIPPING = VoucherType.SHIPPING
    VALUE = VoucherType.VALUE
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
