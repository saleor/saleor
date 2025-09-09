import graphene

from ...discount import (
    DiscountType,
    DiscountValueType,
    PromotionEvents,
    PromotionType,
    RewardType,
    RewardValueType,
    VoucherType,
    error_codes,
)
from ..core.doc_category import DOC_CATEGORY_DISCOUNTS
from ..core.enums import to_enum
from ..directives import doc

OrderDiscountTypeEnum = doc(
    DOC_CATEGORY_DISCOUNTS, to_enum(DiscountType, type_name="OrderDiscountType")
)
RewardValueTypeEnum = doc(
    DOC_CATEGORY_DISCOUNTS, to_enum(RewardValueType, type_name="RewardValueTypeEnum")
)
RewardTypeEnum = doc(
    DOC_CATEGORY_DISCOUNTS, to_enum(RewardType, type_name="RewardTypeEnum")
)
PromotionTypeEnum = doc(
    DOC_CATEGORY_DISCOUNTS, to_enum(PromotionType, type_name="PromotionTypeEnum")
)
PromotionEventsEnum = doc(
    DOC_CATEGORY_DISCOUNTS, to_enum(PromotionEvents, type_name="PromotionEventsEnum")
)

PromotionCreateErrorCode = graphene.Enum.from_enum(error_codes.PromotionCreateErrorCode)
PromotionUpdateErrorCode = graphene.Enum.from_enum(error_codes.PromotionUpdateErrorCode)
PromotionDeleteErrorCode = graphene.Enum.from_enum(error_codes.PromotionDeleteErrorCode)
PromotionRuleCreateErrorCode = graphene.Enum.from_enum(
    error_codes.PromotionRuleCreateErrorCode
)
PromotionRuleUpdateErrorCode = graphene.Enum.from_enum(
    error_codes.PromotionRuleUpdateErrorCode
)
PromotionRuleDeleteErrorCode = graphene.Enum.from_enum(
    error_codes.PromotionRuleDeleteErrorCode
)


@doc(category=DOC_CATEGORY_DISCOUNTS)
class SaleType(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE


@doc(category=DOC_CATEGORY_DISCOUNTS)
class DiscountValueTypeEnum(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE


@doc(category=DOC_CATEGORY_DISCOUNTS)
class VoucherTypeEnum(graphene.Enum):
    SHIPPING = VoucherType.SHIPPING
    ENTIRE_ORDER = VoucherType.ENTIRE_ORDER
    SPECIFIC_PRODUCT = VoucherType.SPECIFIC_PRODUCT


@doc(category=DOC_CATEGORY_DISCOUNTS)
class DiscountStatusEnum(graphene.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"


@doc(category=DOC_CATEGORY_DISCOUNTS)
class VoucherDiscountType(graphene.Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    SHIPPING = "shipping"
