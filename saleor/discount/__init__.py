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
    SHIPPING = "shipping"
    ENTIRE_ORDER = "entire_order"
    SPECIFIC_PRODUCT = "specific_product"

    CHOICES = [
        (ENTIRE_ORDER, pgettext_lazy("Voucher: discount for", "Entire order")),
        (SHIPPING, pgettext_lazy("Voucher: discount for", "Shipping")),
        (
            SPECIFIC_PRODUCT,
            pgettext_lazy(
                "Voucher: discount for", "Specific products, collections and categories"
            ),
        ),
    ]


@dataclass
class DiscountInfo:
    sale: Any
    product_ids: List[int]
    category_ids: List[int]
    collection_ids: List[int]
