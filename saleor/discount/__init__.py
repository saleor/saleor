from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Set, Union

from django.conf import settings

if TYPE_CHECKING:
    # flake8: noqa
    from .models import Sale, Voucher


class DiscountValueType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, settings.DEFAULT_CURRENCY),
        (PERCENTAGE, "%"),
    ]


class VoucherType:
    SHIPPING = "shipping"
    ENTIRE_ORDER = "entire_order"
    SPECIFIC_PRODUCT = "specific_product"

    CHOICES = [
        (ENTIRE_ORDER, "Entire order"),
        (SHIPPING, "Shipping"),
        (SPECIFIC_PRODUCT, "Specific products, collections and categories"),
    ]


@dataclass
class DiscountInfo:
    sale: Union["Sale", "Voucher"]
    product_ids: Union[List[int], Set[int]]
    category_ids: Union[List[int], Set[int]]
    collection_ids: Union[List[int], Set[int]]
