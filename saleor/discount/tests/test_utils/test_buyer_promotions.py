import datetime
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from prices import Money

from ....product.models import Product, VariantChannelListingPromotionRule
from ....product.utils.variant_prices import update_discounted_prices_for_promotion
from ... import RewardValueType
from ...models import PromotionRule
from ...utils.buyer_promotions import (
    calculate_best_discounted_price_for_rules,
    get_best_rule_discount,
    get_buyer_promotion_rules,
)
from ...utils.promotion import fetch_promotion_rules_for_checkout_or_order

CURRENCY = "USD"
RULE_VARIANTS_TABLE = '"discount_promotionrule_variants"'
CHECKOUT_TABLE = '"checkout_checkout"'


def _rule(name, value, value_type=RewardValueType.PERCENTAGE):
    """Build an unsaved rule, which is enough to compute its discount."""
    return PromotionRule(
        name=name, reward_value=Decimal(value), reward_value_type=value_type
    )


def test_get_best_rule_discount_picks_the_largest_discount():
    # given
    price = Money(Decimal(10), CURRENCY)
    percentage_rule = _rule("10 percent", 10)
    fixed_rule = _rule("3 off", 3, RewardValueType.FIXED)
    bigger_percentage_rule = _rule("25 percent", 25)

    # when
    best = get_best_rule_discount(
        price, [percentage_rule, fixed_rule, bigger_percentage_rule], CURRENCY
    )

    # then
    assert best.rule is fixed_rule
    assert best.discount == Money(Decimal(3), CURRENCY)


def test_get_best_rule_discount_keeps_the_first_rule_on_a_tie():
    # given
    price = Money(Decimal(10), CURRENCY)
    stored_rule = _rule("10 percent", 10)
    buyer_rule = _rule("1 off", 1, RewardValueType.FIXED)

    # when
    best = get_best_rule_discount(price, [stored_rule, buyer_rule], CURRENCY)

    # then
    assert best.rule is stored_rule
    assert best.discount == Money(Decimal(1), CURRENCY)


def test_get_best_rule_discount_without_rules_returns_none():
    # when
    best = get_best_rule_discount(Money(Decimal(10), CURRENCY), [], CURRENCY)

    # then
    assert best is None


def test_calculate_best_discounted_price_for_rules_never_goes_below_zero():
    # given
    price = Money(Decimal(10), CURRENCY)
    rule = _rule("15 off", 15, RewardValueType.FIXED)

    # when
    discounted = calculate_best_discounted_price_for_rules(
        price=price, rules=[rule], currency=CURRENCY
    )

    # then
    assert discounted == Money(Decimal(0), CURRENCY)


def test_get_buyer_promotion_rules_for_a_guest_runs_no_query(
    variant, channel_USD, promotion_rule_for_customer_type
):
    # when
    with CaptureQueriesContext(connection) as context:
        rules = get_buyer_promotion_rules([variant.pk], channel_USD.pk, None)

    # then
    assert rules == {}
    assert len(context.captured_queries) == 0


def test_get_buyer_promotion_rules_matches_the_customer_type(
    variant, channel_USD, b2b_customer_user, promotion_rule_for_customer_type
):
    # when
    rules = get_buyer_promotion_rules(
        [variant.pk], channel_USD.pk, b2b_customer_user.pk
    )

    # then
    assert rules == {variant.pk: [promotion_rule_for_customer_type]}
    [rule] = rules[variant.pk]
    assert rule.promotion == promotion_rule_for_customer_type.promotion


def test_get_buyer_promotion_rules_matches_the_attribute_value(
    variant, channel_USD, gold_customer_user, promotion_rule_for_attribute_value
):
    # when
    rules = get_buyer_promotion_rules(
        [variant.pk], channel_USD.pk, gold_customer_user.pk
    )

    # then
    assert rules == {variant.pk: [promotion_rule_for_attribute_value]}


def test_get_buyer_promotion_rules_ignores_a_customer_of_another_type(
    variant, channel_USD, customer_user, promotion_rule_for_customer_type
):
    # when
    rules = get_buyer_promotion_rules([variant.pk], channel_USD.pk, customer_user.pk)

    # then
    assert rules == {}


def test_get_buyer_promotion_rules_ignores_an_ended_promotion(
    variant, channel_USD, b2b_customer_user, promotion_rule_for_customer_type
):
    # given
    promotion = promotion_rule_for_customer_type.promotion
    promotion.end_date = timezone.now() - datetime.timedelta(days=1)
    promotion.save(update_fields=["end_date"])

    # when
    rules = get_buyer_promotion_rules(
        [variant.pk], channel_USD.pk, b2b_customer_user.pk
    )

    # then
    assert rules == {}


def test_get_buyer_promotion_rules_ignores_another_channel(
    variant, channel_PLN, b2b_customer_user, promotion_rule_for_customer_type
):
    # when
    rules = get_buyer_promotion_rules(
        [variant.pk], channel_PLN.pk, b2b_customer_user.pk
    )

    # then
    assert rules == {}


def test_get_buyer_promotion_rules_without_candidates_runs_one_query(
    variant, channel_USD, b2b_customer_user, promotion_rule
):
    # given
    assert promotion_rule.customer_type_conditions.exists() is False

    # when
    with CaptureQueriesContext(connection) as context:
        rules = get_buyer_promotion_rules(
            [variant.pk], channel_USD.pk, b2b_customer_user.pk
        )

    # then
    assert rules == {}
    [query] = context.captured_queries
    assert RULE_VARIANTS_TABLE in query["sql"]


def test_stored_price_ignores_a_rule_with_buyer_conditions(
    product, variant, catalogue_promotion, promotion_rule_for_customer_type
):
    # given
    # the public 10% rule of the promotion and the 25% B2B rule cover the product
    public_rule = catalogue_promotion.rules.get(reward_value=Decimal(10))
    listing = variant.channel_listings.get()
    assert listing.price_amount == Decimal(10)

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))

    # then
    listing.refresh_from_db(fields=["discounted_price_amount"])
    assert listing.discounted_price_amount == Decimal(9)
    listing_rule = VariantChannelListingPromotionRule.objects.get(
        variant_channel_listing=listing
    )
    assert listing_rule.promotion_rule == public_rule


def _store_checkout_base_prices(checkout, amount=100):
    checkout.base_total_amount = amount
    checkout.base_subtotal_amount = amount
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])


def test_fetch_promotion_rules_for_checkout_matches_the_customer_type(
    checkout, b2b_customer_user, order_promotion_rule_for_customer_type
):
    # given
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _store_checkout_base_prices(checkout)

    # when
    rules = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert rules == [order_promotion_rule_for_customer_type]


def test_fetch_promotion_rules_for_checkout_skips_the_predicate_for_a_mismatch(
    checkout, customer_user, order_promotion_rule_for_customer_type
):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    _store_checkout_base_prices(checkout)

    # when
    with CaptureQueriesContext(connection) as context:
        rules = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert rules == []
    predicate_queries = [
        query for query in context.captured_queries if CHECKOUT_TABLE in query["sql"]
    ]
    assert predicate_queries == []


def test_fetch_promotion_rules_for_checkout_with_buyer_conditions_only(
    checkout, b2b_customer_user, order_promotion_rule_for_customer_type
):
    # given
    rule = order_promotion_rule_for_customer_type
    rule.order_predicate = {}
    rule.save(update_fields=["order_predicate"])
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _store_checkout_base_prices(checkout, amount=1)

    # when
    with CaptureQueriesContext(connection) as context:
        rules = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert rules == [rule]
    predicate_queries = [
        query for query in context.captured_queries if CHECKOUT_TABLE in query["sql"]
    ]
    assert predicate_queries == []


def test_fetch_promotion_rules_for_checkout_ignores_buyer_rules_for_a_guest(
    checkout, order_promotion_rule_for_customer_type
):
    # given
    assert checkout.user is None
    _store_checkout_base_prices(checkout)

    # when
    rules = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert rules == []


def test_fetch_promotion_rules_for_checkout_ignores_a_catalogue_rule_with_buyer_conditions(
    checkout, b2b_customer_user, promotion_rule_for_customer_type
):
    # given
    assert promotion_rule_for_customer_type.order_predicate == {}
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _store_checkout_base_prices(checkout)

    # when
    rules = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert rules == []


def test_fetch_promotion_rules_for_checkout_fetches_no_conditions_for_a_guest(
    checkout, order_promotion_rule_for_customer_type
):
    # given
    assert checkout.user is None
    _store_checkout_base_prices(checkout)

    # when
    with CaptureQueriesContext(connection) as context:
        fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    condition_queries = [
        query
        for query in context.captured_queries
        if '"discount_promotionrulecustomertype"' in query["sql"]
        and "EXISTS" not in query["sql"]
    ]
    assert condition_queries == []
