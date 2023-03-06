from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Set, Union

if TYPE_CHECKING:
    from .models import Sale, SaleChannelListing


class DiscountValueType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, "fixed"),
        (PERCENTAGE, "%"),
    ]


class OrderDiscountType:
    VOUCHER = "voucher"
    MANUAL = "manual"
    CHOICES = [(VOUCHER, "Voucher"), (MANUAL, "Manual")]


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
    sale: "Sale"
    channel_listings: Dict[str, "SaleChannelListing"]
    product_ids: Union[List[int], Set[int]]
    category_ids: Union[List[int], Set[int]]
    collection_ids: Union[List[int], Set[int]]
    variants_ids: Union[List[int], Set[int]]
