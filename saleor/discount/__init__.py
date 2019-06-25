from dataclasses import dataclass
from typing import Any, List

from django.conf import settings
from django.utils.translation import pgettext_lazy


class DiscountValueType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, pgettext_lazy("Discount type", settings.DEFAULT_CURRENCY)),
        (PERCENTAGE, pgettext_lazy("Discount type", "%")),
    ]


class VoucherType:
    PRODUCT = "product"
    COLLECTION = "collection"
    CATEGORY = "category"
    SHIPPING = "shipping"
    ENTIRE_ORDER = "entire_order"

    CHOICES = [
        (ENTIRE_ORDER, pgettext_lazy("Voucher: discount for", "Entire order")),
        (PRODUCT, pgettext_lazy("Voucher: discount for", "Specific products")),
        (
            COLLECTION,
            pgettext_lazy("Voucher: discount for", "Specific collections of products"),
        ),
        (
            CATEGORY,
            pgettext_lazy("Voucher: discount for", "Specific categories of products"),
        ),
        (SHIPPING, pgettext_lazy("Voucher: discount for", "Shipping")),
    ]


@dataclass
class DiscountInfo:
    sale: Any
    product_ids: List[int]
    category_ids: List[int]
    collection_ids: List[int]
