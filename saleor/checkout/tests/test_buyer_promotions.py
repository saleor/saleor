from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from prices import Money

from ...discount.interface import VariantPromotionRuleInfo
from ...discount.utils.checkout import (
    create_checkout_discount_objects_for_order_promotions,
    create_checkout_line_discount_objects_for_catalogue_promotions,
)
from ...graphql.checkout.mutations.utils import CheckoutLineData
from ...plugins.manager import get_plugins_manager
from ...product.models import Product
from ...product.utils.variant_prices import update_discounted_prices_for_promotion
from ..base_calculations import calculate_base_line_total_price
from ..fetch import fetch_checkout_info, fetch_checkout_lines
from ..utils import add_variants_to_checkout

RULE_VARIANTS_TABLE = '"discount_promotionrule_variants"'
RULE_CONDITION_TABLES = (
    '"discount_promotionrulecustomertype"',
    '"discount_promotionrulecustomerattributevalue"',
)


def _add_variant(checkout, variant, quantity=1):
    """Add a line through the same path as the checkoutLinesAdd mutation."""
    line_data = CheckoutLineData(variant_id=str(variant.pk), quantity=quantity)
    add_variants_to_checkout(
        checkout,
        [variant],
        [line_data],
        checkout.channel,
        calculate_stocks_with_shipping_zones=True,
    )


def _store_guest_price(product):
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))


def test_fetch_checkout_lines_picks_the_buyer_rule_for_the_customer(
    checkout,
    variant,
    product,
    b2b_customer_user,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    # the public 10% rule is stored, the 25% B2B rule is resolved per buyer
    _store_guest_price(product)
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _add_variant(checkout, variant)
    currency = checkout.currency

    # when
    lines, _ = fetch_checkout_lines(checkout)

    # then
    [line_info] = lines
    [rule_info] = line_info.rules_info
    assert rule_info.rule == promotion_rule_for_customer_type
    assert rule_info.resolved_for_buyer is True
    assert line_info.undiscounted_unit_price == Money(Decimal(10), currency)
    assert line_info.variant_discounted_price == Money(Decimal("7.50"), currency)


def test_fetch_checkout_lines_keeps_the_stored_rule_for_a_guest(
    checkout, variant, product, catalogue_promotion, promotion_rule_for_customer_type
):
    # given
    _store_guest_price(product)
    public_rule = catalogue_promotion.rules.get(reward_value=Decimal(10))
    assert checkout.user is None
    _add_variant(checkout, variant)

    # when
    lines, _ = fetch_checkout_lines(checkout)

    # then
    [line_info] = lines
    [rule_info] = line_info.rules_info
    assert rule_info.rule == public_rule
    assert rule_info.resolved_for_buyer is False
    assert line_info.variant_discounted_price == Money(Decimal(9), checkout.currency)


def test_fetch_checkout_lines_keeps_the_stored_rule_when_it_discounts_more(
    checkout,
    variant,
    product,
    b2b_customer_user,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    _store_guest_price(product)
    public_rule = catalogue_promotion.rules.get(reward_value=Decimal(10))
    buyer_rule = promotion_rule_for_customer_type
    buyer_rule.reward_value = Decimal(5)
    buyer_rule.save(update_fields=["reward_value"])
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _add_variant(checkout, variant)

    # when
    lines, _ = fetch_checkout_lines(checkout)

    # then
    [line_info] = lines
    [rule_info] = line_info.rules_info
    assert rule_info.rule == public_rule
    assert line_info.variant_discounted_price == Money(Decimal(9), checkout.currency)


def test_fetch_checkout_lines_applies_the_buyer_rule_on_the_scoped_price(
    checkout,
    variant,
    product,
    b2b_customer_user,
    catalogue_promotion,
    promotion_rule_for_customer_type,
    variant_channel_listing_price_for_customer_type,
):
    # given
    _store_guest_price(product)
    scoped_price = variant_channel_listing_price_for_customer_type.price
    assert scoped_price.amount == Decimal(8)
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _add_variant(checkout, variant)

    # when
    lines, _ = fetch_checkout_lines(checkout)

    # then
    [line_info] = lines
    [rule_info] = line_info.rules_info
    assert rule_info.rule == promotion_rule_for_customer_type
    assert line_info.undiscounted_unit_price == scoped_price
    assert line_info.variant_discounted_price == Money(Decimal(6), checkout.currency)


def test_catalogue_discount_is_created_for_the_buyer_rule(
    checkout,
    variant,
    product,
    b2b_customer_user,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    _store_guest_price(product)
    quantity = 2
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _add_variant(checkout, variant, quantity)
    lines, _ = fetch_checkout_lines(checkout)
    currency = checkout.currency

    # when
    create_checkout_line_discount_objects_for_catalogue_promotions(lines)

    # then
    lines, _ = fetch_checkout_lines(checkout)
    [line_info] = lines
    [discount] = line_info.discounts
    assert discount.promotion_rule == promotion_rule_for_customer_type
    assert discount.amount == Money(Decimal("2.50") * quantity, currency)
    assert calculate_base_line_total_price(line_info) == Money(
        Decimal("7.50") * quantity, currency
    )


def test_fetch_checkout_lines_without_buyer_rules_queries_the_rule_variants_once(
    checkout_with_item, customer_user
):
    # given
    checkout_with_item.user = customer_user
    checkout_with_item.save(update_fields=["user"])

    # when
    with CaptureQueriesContext(connection) as context:
        lines, _ = fetch_checkout_lines(checkout_with_item)

    # then
    [line_info] = lines
    assert line_info.has_buyer_promotion_rule is False
    rule_variant_queries = [
        query
        for query in context.captured_queries
        if RULE_VARIANTS_TABLE in query["sql"]
    ]
    assert len(rule_variant_queries) == 1
    condition_queries = [
        query
        for table in RULE_CONDITION_TABLES
        for query in context.captured_queries
        if table in query["sql"] and RULE_VARIANTS_TABLE not in query["sql"]
    ]
    assert condition_queries == []


def test_fetch_checkout_lines_for_a_guest_does_not_query_the_rule_variants(
    checkout_with_item, promotion_rule_for_customer_type
):
    # given
    assert checkout_with_item.user is None

    # when
    with CaptureQueriesContext(connection) as context:
        fetch_checkout_lines(checkout_with_item)

    # then
    rule_variant_queries = [
        query
        for query in context.captured_queries
        if RULE_VARIANTS_TABLE in query["sql"]
    ]
    assert rule_variant_queries == []


def test_order_promotion_with_buyer_conditions_only_applies_to_the_customer(
    checkout_with_item, b2b_customer_user, order_promotion_rule_for_customer_type
):
    # given
    rule = order_promotion_rule_for_customer_type
    rule.order_predicate = {}
    rule.save(update_fields=["order_predicate"])
    checkout = checkout_with_item
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    create_checkout_discount_objects_for_order_promotions(
        checkout_info, lines, save=True
    )

    # then
    discount = checkout.discounts.get()
    assert discount.promotion_rule == rule
    assert discount.amount == checkout.base_subtotal * Decimal("0.25")


def test_order_promotion_with_buyer_conditions_skips_a_customer_of_another_type(
    checkout_with_item, customer_user, order_promotion_rule_for_customer_type
):
    # given
    rule = order_promotion_rule_for_customer_type
    rule.order_predicate = {}
    rule.save(update_fields=["order_predicate"])
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    create_checkout_discount_objects_for_order_promotions(
        checkout_info, lines, save=True
    )

    # then
    assert checkout.discounts.exists() is False


def test_gift_line_with_the_gift_reward_info_keeps_the_stored_price(
    checkout_with_item, gift_promotion_rule
):
    # given
    # a gift reward has no stored listing rule either, so it must not be taken
    # for a rule resolved for the buyer
    lines, _ = fetch_checkout_lines(checkout_with_item)
    [line_info] = lines
    line_info.line.is_gift = True
    line_info.rules_info = [
        VariantPromotionRuleInfo(
            rule=gift_promotion_rule,
            variant_listing_promotion_rule=None,
            promotion=gift_promotion_rule.promotion,
            promotion_translation=None,
            rule_translation=None,
        )
    ]
    listing = line_info.channel_listing

    # when
    discounted_price = line_info.variant_discounted_price

    # then
    assert line_info.has_buyer_promotion_rule is False
    assert discounted_price == listing.discounted_price
