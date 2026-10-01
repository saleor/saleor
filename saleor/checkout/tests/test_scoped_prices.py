from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from prices import Money

from ...core.taxes import zero_money
from ...discount.utils.checkout import (
    create_checkout_line_discount_objects_for_catalogue_promotions,
)
from ...graphql.checkout.mutations.utils import CheckoutLineData
from ...plugins.manager import get_plugins_manager
from ...product.models import (
    Product,
    VariantChannelListingPrice,
    VariantChannelListingPriceCustomerType,
)
from ...product.utils.variant_prices import update_discounted_prices_for_promotion
from ...product.utils.variants import fetch_variants_for_promotion_rules
from ...tax import TaxCalculationStrategy
from ...tax.calculations.checkout import update_checkout_prices_with_flat_rates
from ..base_calculations import calculate_base_line_total_price
from ..complete_checkout import create_order_from_checkout
from ..fetch import fetch_checkout_info, fetch_checkout_lines
from ..utils import add_variants_to_checkout

SCOPED_PRICE_TABLES = (
    "product_variantchannellistingprice",
    "product_variantchannellistingpricecustomertype",
    "product_variantchannellistingpriceattributevalue",
)


def _add_variant(checkout, variant, quantity=1, price_override=None):
    """Add a line through the same path as the checkoutLinesAdd mutation."""
    line_data = CheckoutLineData(
        variant_id=str(variant.pk), quantity=quantity, custom_price=price_override
    )
    add_variants_to_checkout(
        checkout,
        [variant],
        [line_data],
        checkout.channel,
        calculate_stocks_with_shipping_zones=True,
    )


def test_add_variant_to_checkout_stores_the_scoped_price_for_the_customer(
    checkout,
    variant,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
):
    # given
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    scoped_price = variant_channel_listing_price_for_customer_type.price

    # when
    _add_variant(checkout, variant)

    # then
    line = checkout.lines.get()
    assert line.undiscounted_unit_price == scoped_price


def test_add_variant_to_checkout_stores_the_listing_price_for_a_guest(
    checkout, variant, variant_channel_listing_price_for_customer_type
):
    # given
    assert checkout.user is None
    listing = variant.channel_listings.get()

    # when
    _add_variant(checkout, variant)

    # then
    line = checkout.lines.get()
    assert line.undiscounted_unit_price == listing.price


def test_add_variant_to_checkout_custom_price_beats_the_scoped_price(
    checkout,
    variant,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
):
    # given
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    price_override = Decimal(12)

    # when
    _add_variant(checkout, variant, price_override=price_override)

    # then
    line = checkout.lines.get()
    assert line.undiscounted_unit_price_amount == price_override


def test_fetch_checkout_lines_attaches_the_scoped_price_for_the_customer(
    checkout,
    variant,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
):
    # given
    _add_variant(checkout, variant)
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    scoped_price = variant_channel_listing_price_for_customer_type.price

    # when
    lines, _ = fetch_checkout_lines(checkout)

    # then
    [line_info] = lines
    assert line_info.scoped_unit_price == scoped_price
    assert line_info.undiscounted_unit_price == scoped_price
    assert line_info.variant_discounted_price == scoped_price


def test_fetch_checkout_lines_leaves_the_listing_price_for_a_guest(
    checkout, variant, variant_channel_listing_price_for_customer_type
):
    # given
    _add_variant(checkout, variant)
    listing = variant.channel_listings.get()

    # when
    lines, _ = fetch_checkout_lines(checkout)

    # then
    [line_info] = lines
    assert line_info.scoped_unit_price is None
    assert line_info.undiscounted_unit_price == listing.price


def test_fetch_checkout_lines_without_rows_queries_the_rows_table_once(
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
    assert line_info.scoped_unit_price is None
    tables_hit = [
        table
        for table in (*SCOPED_PRICE_TABLES, "attribute_assigneduserattributevalue")
        for query in context.captured_queries
        if table in query["sql"]
    ]
    assert tables_hit == ["product_variantchannellistingprice"]


def test_catalogue_discount_is_recomputed_on_the_scoped_price(
    checkout,
    variant,
    product,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
    catalogue_promotion_with_single_rule,
):
    # given
    # the fixed rule of 5 is stored against the listing price of 10
    fetch_variants_for_promotion_rules(catalogue_promotion_with_single_rule.rules.all())
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))
    quantity = 2
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    _add_variant(checkout, variant, quantity)
    lines, _ = fetch_checkout_lines(checkout)
    scoped_price = variant_channel_listing_price_for_customer_type.price
    currency = scoped_price.currency

    # when
    create_checkout_line_discount_objects_for_catalogue_promotions(lines)

    # then
    lines, _ = fetch_checkout_lines(checkout)
    [line_info] = lines
    [discount] = line_info.discounts
    assert discount.amount == Money(Decimal(5) * quantity, currency)
    assert line_info.variant_discounted_price == Money(Decimal(3), currency)
    assert calculate_base_line_total_price(line_info) == Money(
        Decimal(3) * quantity, currency
    )


def test_flat_rate_taxes_are_calculated_on_the_scoped_price(
    checkout,
    variant,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
    channel_USD,
):
    # given
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tax_configuration.prices_entered_with_tax = False
    tax_configuration.save(
        update_fields=["tax_calculation_strategy", "prices_entered_with_tax"]
    )
    tax_rate = Decimal(25)
    tax_class = variant.product.tax_class or variant.product.product_type.tax_class
    tax_class.country_rates.update_or_create(country="US", defaults={"rate": tax_rate})
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    quantity = 2
    _add_variant(checkout, variant, quantity)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    scoped_price = variant_channel_listing_price_for_customer_type.price

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax=False
    )

    # then
    [line_info] = lines
    net = scoped_price * quantity
    assert line_info.line.total_price.net == net
    assert line_info.line.total_price.gross == net * Decimal("1.25")


def test_create_order_from_checkout_copies_the_scoped_price(
    checkout,
    variant,
    stock,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
    app,
):
    # given
    checkout.user = b2b_customer_user
    checkout.billing_address = b2b_customer_user.default_billing_address
    checkout.shipping_address = b2b_customer_user.default_shipping_address
    checkout.save(update_fields=["user", "billing_address", "shipping_address"])
    _add_variant(checkout, variant)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    scoped_price = variant_channel_listing_price_for_customer_type.price

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info, manager=manager, user=None, app=app
    )

    # then
    order_line = order.lines.get()
    assert order_line.undiscounted_base_unit_price == scoped_price
    assert order_line.base_unit_price == scoped_price


def test_fetch_checkout_lines_keeps_the_listing_price_for_a_gift_line(
    checkout_with_item_and_gift_promotion, b2b_customer_user, customer_type
):
    # given
    checkout = checkout_with_item_and_gift_promotion
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    gift_line = checkout.lines.get(is_gift=True)
    gift_listing = gift_line.variant.channel_listings.get(channel=checkout.channel)
    listing_price = VariantChannelListingPrice.objects.create(
        variant_channel_listing=gift_listing,
        currency=gift_listing.currency,
        price_amount=Decimal(8),
    )
    VariantChannelListingPriceCustomerType.objects.create(
        listing_price=listing_price, customer_type=customer_type
    )

    # when
    lines, _ = fetch_checkout_lines(checkout)

    # then
    [gift_line_info] = [line_info for line_info in lines if line_info.line.is_gift]
    assert gift_line_info.scoped_unit_price is None
    assert gift_line_info.undiscounted_unit_price == gift_listing.price
    assert calculate_base_line_total_price(gift_line_info) == zero_money(
        checkout.currency
    )
