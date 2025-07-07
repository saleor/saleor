from decimal import Decimal
from unittest import mock

import pytest
from prices import Money, TaxedMoney

from ...checkout import calculations
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import add_variant_to_checkout
from ...core.prices import quantize_price
from ...core.taxes import zero_taxed_money
from ...discount.utils.checkout import (
    create_checkout_discount_objects_for_order_promotions,
)
from ...plugins.manager import get_plugins_manager
from ...product.models import ProductVariantChannelListing
from ...tax.models import TaxClassCountryRate
from .. import TaxCalculationStrategy
from ..calculations.checkout import (
    _calculate_checkout_line_total,
    _calculate_checkout_shipping,
    update_checkout_prices_with_flat_rates,
)


def _enable_flat_rates(
    checkout, prices_entered_with_tax, use_weighted_tax_for_shipping=False
):
    tc = checkout.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.use_weighted_tax_for_shipping = use_weighted_tax_for_shipping
    tc.save()


@pytest.mark.parametrize(
    (
        "checkout_total_net",
        "checkout_total_gross",
        "gift_card_balance",
        "expected_total_net",
        "expected_total_gross",
    ),
    [
        ("0.00", "0.00", "0.00", "0.00", "0.00"),
        ("0.00", "0.00", "10.00", "0.00", "0.00"),
        ("10.00", "10.00", "5.00", "5.00", "5.00"),  # tax rate = 0%
        ("10.00", "10.00", "10.00", "0.00", "0.00"),  # tax rate = 0%
        ("10.00", "12.00", "10.00", "1.67", "2.00"),  # tax rate = 20%
        ("10.00", "12.00", "12.00", "0.00", "0.00"),  # tax rate = 20%
        ("30.00", "36.00", "12.00", "20", "24.00"),  # tax rate = 20%
    ],
)
@mock.patch("saleor.checkout.calculations.checkout_total")
def test_calculate_checkout_total_with_gift_cards(
    checkout_total_mock,
    checkout_total_net,
    checkout_total_gross,
    gift_card_balance,
    expected_total_net,
    expected_total_gross,
    gift_card,
    checkout_with_gift_card,
    address,
):
    assert not gift_card.last_used_on
    gift_card.current_balance_amount = Decimal(gift_card_balance)
    gift_card.save(update_fields=["current_balance_amount"])

    checkout = checkout_with_gift_card
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    checkout_total_mock.return_value = TaxedMoney(
        net=Money(checkout_total_net, "USD"), gross=Money(checkout_total_gross, "USD")
    )

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    assert total.net == Money(expected_total_net, "USD")
    assert total.gross == Money(expected_total_gross, "USD")


@pytest.mark.parametrize(
    (
        "expected_net",
        "expected_gross",
        "expected_tax_rate",
        "voucher_amount",
        "prices_entered_with_tax",
        "use_weighted_tax_for_shipping",
    ),
    [
        ("40.00", "49.20", "0.230", "0.0", False, False),
        ("30.08", "37.00", "0.230", "3.0", True, False),
        ("40.00", "49.20", "0.230", "0.0", False, True),
        ("30.08", "37.00", "0.230", "3.0", True, True),
    ],
)
def test_calculate_checkout_total(
    checkout_with_item,
    address,
    shipping_zone,
    voucher,
    expected_net,
    expected_gross,
    expected_tax_rate,
    voucher_amount,
    prices_entered_with_tax,
    use_weighted_tax_for_shipping,
):
    # given
    checkout = checkout_with_item
    _enable_flat_rates(checkout, prices_entered_with_tax, use_weighted_tax_for_shipping)

    checkout.shipping_address = address
    voucher_amount = Money(voucher_amount, "USD")
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.voucher_code = voucher.code
    checkout.discount = voucher_amount
    checkout.save()

    line = checkout.lines.first()
    product = line.variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=23)

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address
    )

    # then
    for line_info in lines:
        assert line_info.line.tax_rate == Decimal(expected_tax_rate)
    assert checkout.shipping_tax_rate == Decimal(expected_tax_rate)
    assert checkout.total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    (
        "expected_net",
        "expected_gross",
        "prices_entered_with_tax",
        "use_weighted_tax_for_shipping",
    ),
    [
        ("80.00", "92.40", False, False),
        ("69.78", "80.00", True, False),
        ("80.00", "91.54", False, True),
        ("70.46", "80.00", True, True),
    ],
)
def test_calculate_checkout_total_with_multiple_tax_rates(
    checkout_with_items,
    address,
    shipping_zone,
    tax_classes,
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    use_weighted_tax_for_shipping,
):
    # given
    checkout = checkout_with_items
    _enable_flat_rates(checkout, prices_entered_with_tax, use_weighted_tax_for_shipping)

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    first_line = checkout.lines.first()
    second_line = checkout.lines.last()
    first_line.variant.product.tax_class.country_rates.update_or_create(
        country=address.country, rate=23
    )
    assert first_line.variant.product_id != second_line.variant.product_id

    second_tax_class = tax_classes[0]
    second_tax_class.country_rates.filter(country=address.country).update(rate=3)
    second_line.variant.product.tax_class = second_tax_class
    second_line.variant.product.save()

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    (
        "expected_net",
        "expected_gross",
        "prices_entered_with_tax",
    ),
    [
        ("10.00", "12.30", False),
        ("8.13", "10.00", True),
    ],
)
def test_calculate_checkout_shipping_with_not_weighted_taxes(
    checkout_with_items,
    address,
    shipping_zone,
    tax_classes,
    expected_net,
    expected_gross,
    prices_entered_with_tax,
):
    # given
    checkout = checkout_with_items
    _enable_flat_rates(
        checkout, prices_entered_with_tax, use_weighted_tax_for_shipping=False
    )

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    first_line = checkout.lines.first()
    second_line = checkout.lines.last()
    first_line.variant.product.tax_class.country_rates.update_or_create(
        country=address.country, rate=23
    )
    assert first_line.variant.product_id != second_line.variant.product_id

    second_tax_class = tax_classes[0]
    second_tax_class.country_rates.filter(country=address.country).update(rate=3)
    second_line.variant.product.tax_class = second_tax_class
    second_line.variant.product.save()

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address
    )

    # then
    assert checkout.shipping_tax_rate == Decimal("0.2300")
    assert checkout.shipping_price == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    (
        "expected_net",
        "expected_gross",
        "prices_entered_with_tax",
    ),
    [
        ("10.00", "11.44", False),
        ("8.81", "10.00", True),
    ],
)
def test_calculate_checkout_shipping_with_weighted_taxes(
    checkout_with_items,
    address,
    shipping_zone,
    tax_classes,
    expected_net,
    expected_gross,
    prices_entered_with_tax,
):
    # given
    checkout = checkout_with_items
    _enable_flat_rates(
        checkout, prices_entered_with_tax, use_weighted_tax_for_shipping=True
    )

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    first_line = checkout.lines.first()
    second_line = checkout.lines.last()
    first_line.variant.product.tax_class.country_rates.update_or_create(
        country=address.country, rate=23
    )
    assert first_line.variant.product_id != second_line.variant.product_id

    second_tax_class = tax_classes[0]
    second_tax_class.country_rates.filter(country=address.country).update(rate=3)
    second_line.variant.product.tax_class = second_tax_class
    second_line.variant.product.save()

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address
    )

    # then
    weighted_tax_amount = sum(
        line_info.line.total_price.net.amount * line_info.line.tax_rate
        for line_info in lines
    )
    weighted_tax_amount = weighted_tax_amount / sum(
        line_info.line.total_price.net.amount for line_info in lines
    )
    assert checkout.shipping_tax_rate.quantize(Decimal("0.0001")) == Decimal(
        weighted_tax_amount
    ).quantize(Decimal("0.0001"))
    assert checkout.shipping_price == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("20.33", "25.00", "0.0", True),
        ("20.00", "24.60", "5.0", False),
    ],
)
def test_calculate_checkout_total_with_sale(
    checkout_with_item_on_promotion,
    address,
    shipping_zone,
    voucher,
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
    channel_USD,
):
    # given
    checkout = checkout_with_item_on_promotion
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    voucher_amount = Money(voucher_amount, "USD")
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.voucher_code = voucher.code
    checkout.discount = voucher_amount
    checkout.save()

    line = checkout.lines.first()
    product = line.variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=23)

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout,
        checkout_info,
        lines,
        prices_entered_with_tax,
        address,
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_checkout_total_no_tax_rates(
    checkout_with_item,
    address,
    shipping_zone,
):
    # given
    checkout = checkout_with_item
    prices_entered_with_tax = False
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method = shipping_method
    checkout.save()

    TaxClassCountryRate.objects.all().delete()

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money("40.00", "USD"), gross=Money("40.00", "USD")
    )


def test_calculate_checkout_total_default_tax_rate_for_country(
    checkout_with_item,
    address,
    shipping_zone,
):
    # given
    checkout = checkout_with_item
    prices_entered_with_tax = False
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method = shipping_method
    checkout.save()

    TaxClassCountryRate.objects.all().delete()
    TaxClassCountryRate.objects.create(country=address.country, rate=23)

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money("40.00", "USD"), gross=Money("49.20", "USD")
    )


@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("40.00", "49.20", "0.0", False),
        ("30.08", "37.00", "3.0", True),
    ],
)
def test_calculate_checkout_total_with_shipping_voucher(
    checkout_with_item,
    address,
    shipping_zone,
    voucher_shipping_type,
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
):
    # given
    checkout = checkout_with_item
    _enable_flat_rates(checkout, prices_entered_with_tax)

    manager = get_plugins_manager(allow_replica=False)
    checkout.shipping_address = address
    checkout.save()
    voucher_amount = Money(voucher_amount, "USD")

    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.voucher_code = voucher_shipping_type.code
    checkout.discount = voucher_amount
    checkout.save()

    line = checkout.lines.first()
    product = line.variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=23)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("20.33", "25.00", "0.0", True),
        ("20.00", "24.60", "5.0", False),
    ],
)
def test_calculate_checkout_total_with_shipping_voucher_and_sale(
    checkout_with_item_on_promotion,
    address,
    shipping_zone,
    voucher_shipping_type,
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
):
    # given
    checkout = checkout_with_item_on_promotion
    _enable_flat_rates(checkout, prices_entered_with_tax)

    manager = get_plugins_manager(allow_replica=False)
    checkout.shipping_address = address
    checkout.save()
    voucher_amount = Money(voucher_amount, "USD")

    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.voucher_code = voucher_shipping_type.code
    checkout.discount = voucher_amount
    checkout.save()

    line = checkout.lines.first()
    product = line.variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=23)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout,
        checkout_info,
        lines,
        prices_entered_with_tax,
        address,
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("40.65", "50.00", True),
        ("50.00", "61.50", False),
    ],
)
def test_calculate_checkout_subtotal(
    checkout_with_item,
    address,
    shipping_zone,
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    stock,
):
    # given
    checkout = checkout_with_item
    _enable_flat_rates(checkout, prices_entered_with_tax)

    variant = stock.product_variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=23)

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    update_checkout_prices_with_flat_rates(
        checkout,
        checkout_info,
        lines,
        prices_entered_with_tax,
        address,
    )

    # then
    assert checkout.subtotal == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_checkout_subtotal_with_promotion_prices_entered_with_tax(
    checkout_with_item_on_promotion,
    address,
    shipping_zone,
    stock,
):
    # given
    checkout = checkout_with_item_on_promotion
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    variant = stock.product_variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=23)

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    update_checkout_prices_with_flat_rates(
        checkout,
        checkout_info,
        lines,
        prices_entered_with_tax,
        address,
    )

    # then
    subtotal = Decimal("0.00")
    for line_info in lines:
        subtotal += (
            line_info.channel_listing.discounted_price_amount * line_info.line.quantity
        )
    assert checkout.subtotal == TaxedMoney(
        net=Money(round(subtotal / Decimal("1.23"), 2), "USD"),
        gross=Money(subtotal, "USD"),
    )


def test_calculate_checkout_subtotal_with_promotion_prices_not_entered_with_tax(
    checkout_with_item_on_promotion,
    address,
    shipping_zone,
    stock,
):
    # given
    checkout = checkout_with_item_on_promotion
    prices_entered_with_tax = False
    _enable_flat_rates(checkout, prices_entered_with_tax)

    variant = stock.product_variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=23)

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    update_checkout_prices_with_flat_rates(
        checkout,
        checkout_info,
        lines,
        prices_entered_with_tax,
        address,
    )

    # then
    subtotal = Decimal("0.00")
    for line_info in lines:
        subtotal += (
            line_info.channel_listing.discounted_price_amount * line_info.line.quantity
        )
    assert checkout.subtotal == TaxedMoney(
        net=Money(subtotal, "USD"),
        gross=Money(round(subtotal * Decimal("1.23"), 2), "USD"),
    )


def test_calculate_checkout_subtotal_with_order_promotion(
    checkout_with_item_and_order_discount,
    address,
    shipping_zone,
    stock,
):
    # given
    checkout = checkout_with_item_and_order_discount
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)
    discount_amount = checkout.discounts.first().amount_value

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    update_checkout_prices_with_flat_rates(
        checkout,
        checkout_info,
        lines,
        prices_entered_with_tax,
        address,
    )

    # then
    subtotal = Decimal("0.00")
    for line_info in lines:
        subtotal += (
            line_info.channel_listing.discounted_price_amount * line_info.line.quantity
        )
    discounted_subtotal = subtotal - discount_amount
    assert checkout.subtotal == TaxedMoney(
        net=Money(round(discounted_subtotal / Decimal("1.23"), 2), "USD"),
        gross=Money(discounted_subtotal, "USD"),
    )


def test_calculate_checkout_subtotal_with_gift_promotion(
    checkout_with_item_and_gift_promotion,
    address,
    shipping_zone,
    stock,
):
    # given
    checkout = checkout_with_item_and_gift_promotion
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    update_checkout_prices_with_flat_rates(
        checkout,
        checkout_info,
        lines,
        prices_entered_with_tax,
        address,
    )

    # then
    subtotal = Decimal("0.00")
    for line_info in lines:
        if line_info.line.is_gift:
            continue
        subtotal += (
            line_info.channel_listing.discounted_price_amount * line_info.line.quantity
        )
    assert checkout.subtotal == TaxedMoney(
        net=Money(round(subtotal / Decimal("1.23"), 2), "USD"),
        gross=Money(subtotal, "USD"),
    )


def test_calculate_checkout_line_total(checkout_with_item, shipping_zone, address):
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    line = checkout.lines.first()
    assert line.quantity > 1

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    line_price = _calculate_checkout_line_total(
        checkout_info, lines, checkout_line_info, rate, prices_entered_with_tax
    )

    assert line_price == TaxedMoney(
        net=Money("8.13", "USD") * line.quantity,
        gross=Money("10.00", "USD") * line.quantity,
    )


def test_calculate_checkout_line_total_voucher_on_entire_order(
    checkout_with_item, shipping_zone, address, voucher
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager(allow_replica=False)

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    line = checkout.lines.first()
    assert line.quantity > 1

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    discount_amount = Decimal(5)
    checkout.discount_amount = discount_amount
    checkout.voucher_code = voucher.code
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    channel = checkout.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_price = channel_listing.price * line.quantity

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    # when
    line_price = _calculate_checkout_line_total(
        checkout_info, lines, checkout_line_info, rate, prices_entered_with_tax
    )

    # then
    currency = checkout.currency
    total_gross = Money(total_price.amount - discount_amount, currency)
    unit_net = total_gross / line.quantity / Decimal("1.23")
    assert line_price == TaxedMoney(
        net=quantize_price(unit_net * line.quantity, currency),
        gross=quantize_price(total_gross, currency),
    )


def test_calculate_checkout_line_total_with_voucher_one_line(
    checkout_with_item, shipping_zone, address, voucher
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager(allow_replica=False)
    line = checkout_with_item.lines.first()

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    discount_amount = Decimal(5)
    checkout.discount_amount = discount_amount
    checkout.voucher_code = voucher.code
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    channel = checkout.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_price = channel_listing.price * line.quantity

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    # when
    line_price = _calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        rate,
        prices_entered_with_tax,
    )

    # then
    currency = checkout_with_item.currency
    expected_total_price = quantize_price(
        total_price - Money(discount_amount, currency), currency
    )
    assert line_price == TaxedMoney(
        net=quantize_price(expected_total_price / Decimal("1.23"), currency),
        gross=expected_total_price,
    )


def test_calculate_checkout_line_total_with_voucher_multiple_lines(
    checkout_with_item, shipping_zone, address, voucher, product_list
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout_info = fetch_checkout_info(checkout, [], manager)
    variant_1 = product_list[0].variants.last()
    variant_2 = product_list[1].variants.last()
    qty_1 = 2
    qty_2 = 3
    add_variant_to_checkout(checkout_info, variant_1, qty_1)
    add_variant_to_checkout(checkout_info, variant_2, qty_2)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    discount_amount = Decimal(5)
    checkout.discount_amount = discount_amount
    checkout.voucher_code = voucher.code
    checkout.save()

    line = checkout.lines.first()
    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    channel = checkout.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_line_price = channel_listing.price * line.quantity

    total_unit_prices = (
        variant_1.channel_listings.get(channel=channel).price * qty_1
        + variant_2.channel_listings.get(channel=channel).price * qty_2
        + total_line_price
    )

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    # when
    line_total_price = _calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        rate,
        prices_entered_with_tax,
    )

    # then
    currency = checkout.currency
    discount_amount_for_first_line = quantize_price(
        total_line_price / total_unit_prices * discount_amount, currency
    )
    expected_total_line_price = total_line_price - Money(
        discount_amount_for_first_line, currency
    )
    assert line_total_price == TaxedMoney(
        net=quantize_price(expected_total_line_price / Decimal("1.23"), currency),
        gross=quantize_price(expected_total_line_price, currency),
    )


def test_calculate_checkout_line_total_with_voucher_multiple_lines_last_line(
    checkout_with_item, shipping_zone, address, voucher, product_list
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    currency = checkout.currency

    checkout_info = fetch_checkout_info(checkout, [], manager)
    variant_1 = product_list[0].variants.last()
    variant_2 = product_list[1].variants.last()
    qty_1 = 2
    qty_2 = 3
    add_variant_to_checkout(checkout_info, variant_1, qty_1)
    add_variant_to_checkout(checkout_info, variant_2, qty_2)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    discount_amount = Decimal(5)
    checkout.discount_amount = discount_amount
    checkout.voucher_code = voucher.code
    checkout.save()

    line = checkout.lines.last()
    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    channel = checkout.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_line_price = channel_listing.price * line.quantity

    total_unit_prices = Money(
        sum(
            [
                line.variant.channel_listings.get(channel=channel).price.amount
                * line.quantity
                for line in checkout.lines.all()
            ]
        ),
        currency,
    )

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[-1]

    # when
    line_total_price = _calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        rate,
        prices_entered_with_tax,
    )

    # then
    discount_amount_for_last_line = (
        discount_amount
        - (total_unit_prices - total_line_price) / total_unit_prices * discount_amount
    )
    expected_total_line_price = total_line_price - Money(
        discount_amount_for_last_line, currency
    )
    assert line_total_price == TaxedMoney(
        net=quantize_price(expected_total_line_price / Decimal("1.23"), currency),
        gross=quantize_price(expected_total_line_price, currency),
    )


def test_calculate_checkout_line_total_with_voucher_for_multiple_lines(
    checkout, shipping_zone, address, voucher, product_list
):
    # given
    manager = get_plugins_manager(allow_replica=False)

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    currency = checkout.currency

    # prepare the checkout with line prices and discount value that might
    # result in rounding issues
    checkout_info = fetch_checkout_info(checkout, [], manager)
    variant_1 = product_list[0].variants.last()
    variant_2 = product_list[1].variants.last()
    variant_3 = product_list[2].variants.last()

    variant_ids = [variant_1.id, variant_2.id, variant_3.id]
    channel_listings = list(
        ProductVariantChannelListing.objects.filter(
            variant_id__in=variant_ids, channel_id=checkout.channel_id
        )
    )

    line_prices = [7, 33, 25]
    for listing in channel_listings:
        price = line_prices[variant_ids.index(listing.variant_id)]
        listing.price_amount = price
        listing.discounted_price_amount = price

    ProductVariantChannelListing.objects.bulk_update(
        channel_listings, ["price_amount", "discounted_price_amount"]
    )

    qty = 1
    add_variant_to_checkout(checkout_info, variant_1, qty)
    add_variant_to_checkout(checkout_info, variant_2, qty)
    add_variant_to_checkout(checkout_info, variant_3, qty)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    discount_amount = Decimal(3)
    checkout.discount_amount = discount_amount
    checkout.voucher_code = voucher.code
    checkout.save()

    line = checkout.lines.last()
    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    total_price = Money(sum(line_prices), currency)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    result_total_prices = []
    for line_info in lines:
        result_total_prices.append(
            _calculate_checkout_line_total(
                checkout_info,
                lines,
                line_info,
                rate,
                prices_entered_with_tax,
            )
        )

    # then
    remaining_discount = discount_amount
    assert (
        sum(line_prices)
        - sum([total_price.gross.amount for total_price in result_total_prices])
        == discount_amount
    )
    for idx, line_total_price in enumerate(result_total_prices):
        base_price = line_prices[idx]
        line_base_total = Money(base_price, currency)
        if idx < len(lines) - 1:
            line_discount_amount = quantize_price(
                discount_amount * line_base_total / total_price, currency
            )
            remaining_discount -= line_discount_amount
        else:
            line_discount_amount = remaining_discount

        expected_total_line_price = line_base_total - Money(
            line_discount_amount, currency
        )
        assert line_total_price == TaxedMoney(
            net=quantize_price(expected_total_line_price / Decimal("1.23"), currency),
            gross=quantize_price(expected_total_line_price, currency),
        )


def test_calculate_checkout_line_total_with_shipping_voucher(
    checkout_with_item,
    shipping_zone,
    address,
    voucher_shipping_type,
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    line = checkout.lines.first()

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.discount_amount = Decimal(5)
    checkout.voucher_code = voucher_shipping_type.code
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    channel = checkout.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    unit_gross = channel_listing.price
    expected_total_line_price = unit_gross * line.quantity

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    # when
    line_total_price = _calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        rate,
        prices_entered_with_tax,
    )

    # then
    currency = checkout_with_item.currency
    assert line_total_price == TaxedMoney(
        net=quantize_price(expected_total_line_price / Decimal("1.23"), currency),
        gross=expected_total_line_price,
    )


def test_calculate_checkout_line_total_discount_from_order_promotion(
    checkout_with_item_and_order_discount, shipping_zone, address
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_and_order_discount

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    line = checkout.lines.first()
    assert line.quantity > 1

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]
    create_checkout_discount_objects_for_order_promotions(checkout_info, lines)

    # when
    line_price = _calculate_checkout_line_total(
        checkout_info, lines, checkout_line_info, rate, prices_entered_with_tax
    )

    # then
    variant_listing = variant.channel_listings.get(channel=checkout.channel)
    unit_price = variant.get_price(variant_listing)
    total_price = unit_price * line.quantity
    rule = checkout.discounts.first().promotion_rule
    rule_reward = Money(rule.reward_value, checkout.currency)
    assert line_price == TaxedMoney(
        net=quantize_price(
            (total_price - rule_reward) / Decimal("1.23"), checkout.currency
        ),
        gross=total_price - rule_reward,
    )


def test_calculate_checkout_line_total_discount_for_gift_line(
    checkout_with_item_and_gift_promotion, shipping_zone, address
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_and_gift_promotion

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    line = checkout.lines.get(is_gift=True)
    assert line.quantity == 1

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = [line_info for line_info in lines if line_info.line.is_gift][0]
    create_checkout_discount_objects_for_order_promotions(checkout_info, lines)

    # when
    line_price = _calculate_checkout_line_total(
        checkout_info, lines, checkout_line_info, rate, prices_entered_with_tax
    )

    # then
    assert line_price == zero_taxed_money(checkout.currency)


def test_calculate_checkout_shipping(
    checkout_with_item,
    shipping_zone,
    address,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager(allow_replica=False)
    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method.tax_class.country_rates.update_or_create(
        country=address.country, rate=rate
    )
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    shipping_price = _calculate_checkout_shipping(
        checkout_info, lines, rate, prices_entered_with_tax
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


def test_calculate_checkout_shipping_no_shipping_price(
    checkout_with_item,
    address,
    warehouse_for_cc,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager(allow_replica=False)
    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["shipping_address", "collection_point"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    shipping_price = _calculate_checkout_shipping(
        checkout_info, lines, rate, prices_entered_with_tax
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("0.00", "USD"), gross=Money("0.00", "USD")
    )


def test_calculate_checkout_shipping_voucher_on_shipping(
    checkout_with_item,
    shipping_zone,
    address,
    voucher_shipping_type,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager(allow_replica=False)
    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method = shipping_method
    checkout.shipping_method.tax_class.country_rates.update_or_create(
        country=address.country, rate=rate
    )
    checkout.voucher_code = voucher_shipping_type.code
    discount_amount = Decimal("5.0")
    checkout.discount_amount = discount_amount
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    channel = checkout.channel
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    price = shipping_channel_listings.price

    # when
    shipping_price = _calculate_checkout_shipping(
        checkout_info, lines, rate, prices_entered_with_tax
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    currency = checkout.currency
    expected_gross_shipping_price = Money(price.amount - discount_amount, currency)
    assert shipping_price == TaxedMoney(
        net=quantize_price(expected_gross_shipping_price / Decimal(1.23), currency),
        gross=expected_gross_shipping_price,
    )


def test_calculate_checkout_shipping_free_shipping_voucher(
    checkout_with_item,
    shipping_zone,
    address,
    voucher_shipping_type,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager(allow_replica=False)
    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method = shipping_method
    checkout.shipping_method.tax_class.country_rates.update_or_create(
        country=address.country, rate=rate
    )
    checkout.voucher_code = voucher_shipping_type.code
    channel = checkout.channel
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    price = shipping_channel_listings.price
    checkout.discount_amount = price.amount
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    shipping_price = _calculate_checkout_shipping(
        checkout_info, lines, rate, prices_entered_with_tax
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == zero_taxed_money(checkout.currency)


def test_calculate_checkout_shipping_free_entire_order_voucher(
    checkout_with_item,
    shipping_zone,
    address,
    voucher,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager(allow_replica=False)
    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method = shipping_method
    checkout.shipping_method.tax_class.country_rates.update_or_create(
        country=address.country, rate=rate
    )
    checkout.voucher_code = voucher.code
    channel = checkout.channel
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    discount_amount = Decimal("5.0")
    checkout.discount_amount = discount_amount
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    shipping_price = _calculate_checkout_shipping(
        checkout_info, lines, rate, prices_entered_with_tax
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert (
        shipping_price
        == shipping_price
        == TaxedMoney(
            net=quantize_price(
                shipping_channel_listings.price / Decimal(1.23),
                checkout.currency,
            ),
            gross=shipping_channel_listings.price,
        )
    )
