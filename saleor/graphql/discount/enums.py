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
from ..core.types import BaseEnum

OrderDiscountTypeEnum = to_enum(DiscountType, type_name="OrderDiscountType")
OrderDiscountTypeEnum.doc_category = DOC_CATEGORY_DISCOUNTS
RewardValueTypeEnum = to_enum(RewardValueType, type_name="RewardValueTypeEnum")
RewardValueTypeEnum.doc_category = DOC_CATEGORY_DISCOUNTS
RewardTypeEnum = to_enum(RewardType, type_name="RewardTypeEnum")
RewardTypeEnum.doc_category = DOC_CATEGORY_DISCOUNTS
PromotionTypeEnum = to_enum(PromotionType, type_name="PromotionTypeEnum")
PromotionTypeEnum.doc_category = DOC_CATEGORY_DISCOUNTS
PromotionEventsEnum = to_enum(PromotionEvents, type_name="PromotionEventsEnum")
PromotionEventsEnum.doc_category = DOC_CATEGORY_DISCOUNTS

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


class SaleType(BaseEnum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class DiscountValueTypeEnum(BaseEnum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class VoucherTypeEnum(BaseEnum):
    SHIPPING = VoucherType.SHIPPING
    ENTIRE_ORDER = VoucherType.ENTIRE_ORDER
    SPECIFIC_PRODUCT = VoucherType.SPECIFIC_PRODUCT

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class DiscountStatusEnum(BaseEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class VoucherDiscountType(BaseEnum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    SHIPPING = "shipping"

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
