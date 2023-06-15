from ...discount import DiscountType, DiscountValueType, VoucherType
from ..core.doc_category import DOC_CATEGORY_DISCOUNTS
from ..core.enums import to_enum
from ..core.types import BaseEnum

OrderDiscountTypeEnum = to_enum(DiscountType, type_name="OrderDiscountType")
OrderDiscountTypeEnum.doc_category = DOC_CATEGORY_DISCOUNTS


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
