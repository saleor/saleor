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


class PromoCodeRejectionReason(Enum):
    """Specific reason why a promo code cannot be applied.

    Complements the coarse GraphQL error codes (`INVALID`,
    `VOUCHER_NOT_APPLICABLE`), which stay unchanged, so a storefront can render
    a precise message instead of a generic "voucher is not applicable".

    Most values describe voucher conditions, but the vocabulary is shared with
    gift cards so that a rejection is reported the same way whichever kind of
    promo code was submitted -- the field name alone must not reveal which.

    Submitting a code that matches nothing must stay indistinguishable from
    submitting one that exists but cannot be used, otherwise the response is an
    oracle for guessing codes. So before a code is known to be usable only
    `NOT_FOUND`, `EXPIRED` and `USAGE_LIMIT_REACHED` may be reported -- the
    latter two are a deliberate product decision to help shoppers holding a
    real code. Everything else is reported only once the code is proven live
    (a voucher accepted onto the checkout, a gift card already attached to it),
    where the caller has demonstrably seen the code work and there is nothing
    left to disclose. No reason depends on the caller's permissions.
    """

    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    USAGE_LIMIT_REACHED = "usage_limit_reached"
    NOT_APPLICABLE = "not_applicable"
    MIN_SPENT_NOT_REACHED = "min_spent_not_reached"
    MIN_QUANTITY_NOT_REACHED = "min_quantity_not_reached"
    CUSTOMER_EMAIL_REQUIRED = "customer_email_required"
    SHIPPING_NOT_REQUIRED = "shipping_not_required"
    DELIVERY_METHOD_NOT_SET = "delivery_method_not_set"
    NO_ELIGIBLE_LINES = "no_eligible_lines"
    NO_LONGER_AVAILABLE = "no_longer_available"


NOT_APPLICABLE_MESSAGE = "This offer cannot be applied."
"""Message paired with `PromoCodeRejectionReason.NOT_APPLICABLE`.

Kept as vague as the reason it accompanies: a message naming the condition
(staff-only, already redeemed, another country or channel) would disclose
through the error text exactly what the generic reason withholds.
"""


@dataclass
class PromoCodeRejection:
    """Structured details about why a promo code was rejected."""

    reason: PromoCodeRejectionReason
    min_spent: Money | None = None
    min_checkout_items_quantity: int | None = None


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
