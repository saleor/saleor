from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from prices import Money

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


class VoucherRejectionReason(Enum):
    """Specific reason why a voucher code cannot be applied.

    Complements the coarse GraphQL error codes (`INVALID`,
    `VOUCHER_NOT_APPLICABLE`), which stay unchanged, so a storefront can render
    a precise message instead of a generic "voucher is not applicable".
    """

    NOT_FOUND = "not_found"
    CODE_DEACTIVATED = "code_deactivated"
    NOT_STARTED = "not_started"
    EXPIRED = "expired"
    USAGE_LIMIT_REACHED = "usage_limit_reached"
    NOT_AVAILABLE_IN_CHANNEL = "not_available_in_channel"
    MIN_SPENT_NOT_REACHED = "min_spent_not_reached"
    MIN_QUANTITY_NOT_REACHED = "min_quantity_not_reached"
    ALREADY_USED_BY_CUSTOMER = "already_used_by_customer"
    CUSTOMER_EMAIL_REQUIRED = "customer_email_required"
    STAFF_ONLY = "staff_only"
    SHIPPING_NOT_REQUIRED = "shipping_not_required"
    DELIVERY_METHOD_NOT_SET = "delivery_method_not_set"
    COUNTRY_NOT_ELIGIBLE = "country_not_eligible"
    NO_ELIGIBLE_LINES = "no_eligible_lines"
    NO_LONGER_AVAILABLE = "no_longer_available"


@dataclass
class VoucherRejection:
    """Structured details about why a voucher code was rejected."""

    reason: VoucherRejectionReason
    min_spent: Money | None = None
    min_checkout_items_quantity: int | None = None
    countries: list[str] | None = None


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
