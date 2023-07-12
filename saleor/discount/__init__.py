from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Set, Union

from django.db.models import QuerySet

from ..core.types import EventTypeBase

if TYPE_CHECKING:
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


class PromotionEvents(EventTypeBase):
    PROMOTION_CREATED = "promotion_event_created"
    PROMOTION_UPDATED = "promotion_event_updated"
    PROMOTION_STARTED = "promotion_event_started"
    PROMOTION_ENDED = "promotion_event_ended"

    RULE_CREATED = "promotion_event_rule_created"
    RULE_UPDATED = "promotion_event_rule_updated"
    RULE_DELETED = "promotion_event_rule_deleted"

    CHOICES = [
        (PROMOTION_CREATED, "Promotion created"),
        (PROMOTION_UPDATED, "Promotion updated"),
        (PROMOTION_STARTED, "Promotion started"),
        (PROMOTION_ENDED, "Promotion ended"),
        (RULE_CREATED, "Rule created"),
        (RULE_UPDATED, "Rule updated"),
        (RULE_DELETED, "Rule deleted"),
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
    channel_ids: List[int]
