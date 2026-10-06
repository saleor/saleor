import datetime
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from freezegun import freeze_time
from prices import Money

from ...discount import RewardValueType
from ...discount.interface import VariantPromotionRuleInfo
from ...discount.models import PromotionRule
from ...graphql.order.utils import OrderLineData
from ...product.models import (
    VariantChannelListingPrice,
    VariantChannelListingPriceCustomerType,
)
from .. import OrderStatus
from ..calculations import refresh_order_base_prices_and_discounts
from ..fetch import fetch_draft_order_lines_info
from ..utils import (
    attach_buyer_pricing_to_lines_data,
    create_order_line,
    expire_draft_order_line_prices,
)

SCOPED_AMOUNT = Decimal(8)
SCOPED_PRICE_ROWS_TABLE = '"product_variantchannellistingprice"'


def _scope_listing_to_type(listing, customer_type, amount=SCOPED_AMOUNT):
    listing_price = VariantChannelListingPrice.objects.create(
        variant_channel_listing=listing,
        currency=listing.currency,
        price_amount=amount,
    )
    VariantChannelListingPriceCustomerType.objects.create(
        listing_price=listing_price, customer_type=customer_type
    )
    return listing_price


def test_attach_buyer_pricing_to_lines_data_resolves_every_line_in_one_batch(
    draft_order, variant, product_without_shipping, b2b_customer_user, customer_type
):
    # given
    order = draft_order
    order.user = b2b_customer_user
    order.save(update_fields=["user"])
    listing = variant.channel_listings.get()
    _scope_listing_to_type(listing, customer_type)
    other_variant = product_without_shipping.variants.first()
    lines_data = [
        OrderLineData(variant=variant, quantity=1),
        OrderLineData(variant=other_variant, quantity=1),
    ]

    # when
    with CaptureQueriesContext(connection) as context:
        attach_buyer_pricing_to_lines_data(order, lines_data)

    # then
    [line_data, other_line_data] = lines_data
    assert line_data.scoped_price == Money(SCOPED_AMOUNT, listing.currency)
    assert other_line_data.scoped_price is None
    rows_queries = [
        query
        for query in context.captured_queries
        if SCOPED_PRICE_ROWS_TABLE in query["sql"]
    ]
    assert len(rows_queries) == 1


def test_attach_buyer_pricing_to_lines_data_ignores_rows_for_an_order_without_user(
    draft_order, variant, customer_type
):
    # given
    order = draft_order
    order.user = None
    order.save(update_fields=["user"])
    listing = variant.channel_listings.get()
    _scope_listing_to_type(listing, customer_type)
    line_data = OrderLineData(variant=variant, quantity=1)

    # when
    attach_buyer_pricing_to_lines_data(order, [line_data])

    # then
    assert line_data.scoped_price is None


def test_create_order_line_uses_the_scoped_price_of_the_line_data(
    draft_order, variant, site_settings
):
    # given
    order = draft_order
    listing = variant.channel_listings.get()
    scoped_price = Money(SCOPED_AMOUNT, listing.currency)
    line_data = OrderLineData(variant=variant, quantity=2, scoped_price=scoped_price)

    # when
    line = create_order_line(order, line_data, None, site_settings)

    # then
    assert line.undiscounted_base_unit_price == scoped_price
    assert line.base_unit_price == scoped_price
    assert line.unit_price.net == scoped_price


def test_create_order_line_without_a_scoped_price_uses_the_listing_price(
    draft_order, variant, site_settings
):
    # given
    order = draft_order
    listing = variant.channel_listings.get()
    line_data = OrderLineData(variant=variant, quantity=1)

    # when
    line = create_order_line(order, line_data, None, site_settings)

    # then
    assert line.undiscounted_base_unit_price == listing.price


def test_create_order_line_reapplies_the_promotion_on_the_scoped_price(
    draft_order, variant, site_settings, catalogue_promotion_without_rules
):
    # given
    order = draft_order
    listing = variant.channel_listings.get()
    rule = PromotionRule.objects.create(
        promotion=catalogue_promotion_without_rules,
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
    )
    rule.channels.add(order.channel)
    listing_rule = listing.variantlistingpromotionrule.create(
        promotion_rule=rule, discount_amount=Decimal(5), currency=listing.currency
    )
    rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]
    quantity = 2
    currency = listing.currency
    line_data = OrderLineData(
        variant=variant,
        quantity=quantity,
        rules_info=rules_info,
        scoped_price=Money(SCOPED_AMOUNT, currency),
    )

    # when
    line = create_order_line(order, line_data, None, site_settings)

    # then
    assert line.undiscounted_base_unit_price == Money(SCOPED_AMOUNT, currency)
    assert line.base_unit_price == Money(Decimal(3), currency)
    [discount] = line.discounts.all()
    assert discount.amount == Money(Decimal(5) * quantity, currency)


def test_refresh_order_base_prices_uses_the_scoped_price(
    draft_order, b2b_customer_user, customer_type
):
    # given
    order = draft_order
    order.user = b2b_customer_user
    order.save(update_fields=["user"])
    line_1, line_2 = order.lines.all()
    listing_1 = line_1.variant.channel_listings.get()
    _scope_listing_to_type(listing_1, customer_type)
    listing_2 = line_2.variant.channel_listings.get()
    scoped_price = Money(SCOPED_AMOUNT, listing_1.currency)

    # when
    refresh_order_base_prices_and_discounts(order, [line_1.pk, line_2.pk])

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price == scoped_price
    assert line_1.base_unit_price == scoped_price
    assert line_2.undiscounted_base_unit_price == listing_2.price
    assert line_2.base_unit_price == listing_2.price


def test_fetch_draft_order_lines_info_keeps_the_listing_price_for_a_gift_line(
    order_with_lines_and_gift_promotion, b2b_customer_user, customer_type
):
    # given
    order = order_with_lines_and_gift_promotion
    order.user = b2b_customer_user
    order.save(update_fields=["user"])
    gift_line = order.lines.get(is_gift=True)
    gift_listing = gift_line.variant.channel_listings.get(channel=order.channel)
    _scope_listing_to_type(gift_listing, customer_type)

    # when
    lines_info = fetch_draft_order_lines_info(order, fetch_actual_prices=True)

    # then
    [gift_line_info] = [line_info for line_info in lines_info if line_info.line.is_gift]
    assert gift_line_info.channel_listing == gift_listing
    assert gift_line_info.scoped_unit_price is None


def test_refresh_order_base_prices_ignores_scoped_rows_for_a_guest_order(
    draft_order, customer_type
):
    # given
    order = draft_order
    order.user = None
    order.save(update_fields=["user"])
    [line_1, _] = order.lines.all()
    listing_1 = line_1.variant.channel_listings.get()
    _scope_listing_to_type(listing_1, customer_type)

    # when
    refresh_order_base_prices_and_discounts(order, [line_1.pk])

    # then
    line_1 = order.lines.get(pk=line_1.pk)
    assert line_1.undiscounted_base_unit_price == listing_1.price


@freeze_time("2026-09-15 12:00:00")
def test_expire_draft_order_line_prices_skips_lines_with_a_custom_price(draft_order):
    # given
    order = draft_order
    line_1, line_2 = order.lines.all()
    line_2.is_price_overridden = True
    line_2.draft_base_price_expire_at = None
    line_2.save(update_fields=["is_price_overridden", "draft_base_price_expire_at"])
    line_1.draft_base_price_expire_at = timezone.now() + datetime.timedelta(days=1)
    line_1.save(update_fields=["draft_base_price_expire_at"])

    # when
    expire_draft_order_line_prices(order)

    # then
    line_1.refresh_from_db(fields=["draft_base_price_expire_at"])
    line_2.refresh_from_db(fields=["draft_base_price_expire_at"])
    assert line_1.draft_base_price_expire_at == timezone.now()
    assert line_2.draft_base_price_expire_at is None


def test_expire_draft_order_line_prices_ignores_non_draft_orders(order_with_lines):
    # given
    order = order_with_lines
    assert order.status == OrderStatus.UNFULFILLED
    line = order.lines.first()
    line.draft_base_price_expire_at = None
    line.save(update_fields=["draft_base_price_expire_at"])

    # when
    expire_draft_order_line_prices(order)

    # then
    line.refresh_from_db(fields=["draft_base_price_expire_at"])
    assert line.draft_base_price_expire_at is None
