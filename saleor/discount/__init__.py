from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Set, Union

from django.db.models import QuerySet

if TYPE_CHECKING:
    from ..channel.models import Channel
    from .models import PromotionRule, Sale, SaleChannelListing


class DiscountValueType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, "fixed"),
        (PERCENTAGE, "%"),
    ]


class DiscountType:
    SALE = "sale"
    VOUCHER = "voucher"
    MANUAL = "manual"
    CHOICES = [(SALE, "Sale"), (VOUCHER, "Voucher"), (MANUAL, "Manual")]


class VoucherType:
    SHIPPING = "shipping"
    ENTIRE_ORDER = "entire_order"
    SPECIFIC_PRODUCT = "specific_product"

    CHOICES = [
        (ENTIRE_ORDER, "Entire order"),
        (SHIPPING, "Shipping"),
        (SPECIFIC_PRODUCT, "Specific products, collections and categories"),
    ]


class RewardValueType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, "fixed"),
        (PERCENTAGE, "%"),
    ]


@dataclass
class DiscountInfo:
    sale: "Sale"
    channel_listings: Dict[str, "SaleChannelListing"]
    product_ids: Union[List[int], Set[int]]
    category_ids: Union[List[int], Set[int]]
    collection_ids: Union[List[int], Set[int]]
    variants_ids: Union[List[int], Set[int]]


@dataclass
class PromotionRuleInfo:
    rule: "PromotionRule"
    variant_ids: List[int]
    variants: QuerySet
    channels: List["Channel"]
