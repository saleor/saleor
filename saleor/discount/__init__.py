from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import PromotionRule


class DiscountValueType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, "fixed"),
        (PERCENTAGE, "%"),
    ]


class DiscountType:
    SALE = "sale"
    PROMOTION = "promotion"
    ORDER_PROMOTION = "order_promotion"
    VOUCHER = "voucher"
    MANUAL = "manual"

    CHOICES = [
        (SALE, "Sale"),
        (VOUCHER, "Voucher"),
        (MANUAL, "Manual"),
        (PROMOTION, "Promotion"),
        (ORDER_PROMOTION, "Order promotion"),
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


class PromotionType:
    CATALOGUE = "catalogue"
    ORDER = "order"

    CHOICES = [
        (CATALOGUE, "Catalogue"),
        (ORDER, "Order"),
    ]


class RewardValueType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, "fixed"),
        (PERCENTAGE, "%"),
    ]


class RewardType:
    SUBTOTAL_DISCOUNT = "subtotal_discount"
    GIFT = "gift"

    CHOICES = [
        (SUBTOTAL_DISCOUNT, "subtotal_discount"),
        (GIFT, "gift"),
    ]


class PromotionEvents:
    PROMOTION_CREATED = "promotion_created"
    PROMOTION_UPDATED = "promotion_updated"
    PROMOTION_STARTED = "promotion_started"
    PROMOTION_ENDED = "promotion_ended"

    RULE_CREATED = "rule_created"
    RULE_UPDATED = "rule_updated"
    RULE_DELETED = "rule_deleted"

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
class PromotionRuleInfo:
    rule: "PromotionRule"
    channel_ids: list[int]
