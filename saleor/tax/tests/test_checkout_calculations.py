from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import add_variant_to_checkout
from ...core.prices import quantize_price
from ...core.taxes import zero_taxed_money
from ...plugins.manager import get_plugins_manager
from ...tax.models import TaxClassCountryRate
from .. import TaxCalculationStrategy
from ..calculations.checkout import (
    _calculate_checkout_line_unit_price,
    calculate_checkout_line_total,
    calculate_checkout_shipping,
    update_checkout_prices_with_flat_rates,
)


def _enable_flat_rates(checkout, prices_entered_with_tax):
    tc = checkout.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, "
    "prices_entered_with_tax",
    [
        (True, "20.33", "25.00", "0.0", True),
        (True, "20.00", "24.60", "5.0", False),
        (False, "40.00", "49.20", "0.0", False),
        (False, "30.08", "37.00", "3.0", True),
    ],
)
def test_calculate_checkout_total(
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    voucher,
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
):
    # given
    checkout = checkout_with_item
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

    discounts = [discount_info] if with_discount else None
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address, discounts
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
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address, []
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
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address, []
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money("40.00", "USD"), gross=Money("49.20", "USD")
    )


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, "
    "prices_entered_with_tax",
    [
        (True, "20.33", "25.00", "0.0", True),
        (True, "20.00", "24.60", "5.0", False),
        (False, "40.00", "49.20", "0.0", False),
        (False, "30.08", "37.00", "3.0", True),
    ],
)
def test_calculate_checkout_total_shipping_voucher(
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    voucher_shipping_type,
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
):
    # given
    checkout = checkout_with_item
    _enable_flat_rates(checkout, prices_entered_with_tax)

    manager = get_plugins_manager()
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

    discounts = [discount_info] if with_discount else None
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address, discounts
    )

    # then
    assert checkout.total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, prices_entered_with_tax",
    [
        (True, "20.33", "25.00", True),
        (False, "40.65", "50.00", True),
        (True, "25.00", "30.75", False),
        (False, "50.00", "61.50", False),
    ],
)
def test_calculate_checkout_subtotal(
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    with_discount,
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

    discounts = [discount_info] if with_discount else None
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], discounts, manager)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    update_checkout_prices_with_flat_rates(
        checkout, checkout_info, lines, prices_entered_with_tax, address, discounts
    )

    # then
    assert checkout.subtotal == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_checkout_line_total(checkout_with_item, shipping_zone, address):
    manager = get_plugins_manager()
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
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_line_info = lines[0]

    line_price = calculate_checkout_line_total(
        checkout_info, lines, checkout_line_info, [], rate, prices_entered_with_tax
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
    manager = get_plugins_manager()

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
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = calculate_checkout_line_total(
        checkout_info, lines, checkout_line_info, [], rate, prices_entered_with_tax
    )

    # then
    currency = checkout.currency
    total_gross = Money(total_price.amount - discount_amount, currency)
    unit_net = total_gross / line.quantity / Decimal("1.23")
    assert line_price == TaxedMoney(
        net=quantize_price(unit_net * line.quantity, currency),
        gross=quantize_price(total_gross, currency),
    )


def test_calculate_checkout_line_unit_price(checkout_with_item, shipping_zone, address):
    # given
    manager = get_plugins_manager()
    checkout = checkout_with_item
    channel = checkout.channel
    line = checkout_with_item.lines.first()

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = _calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        channel,
        [],
        rate,
        prices_entered_with_tax,
    )

    # then
    assert quantize_price(line_price, line_price.currency) == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


def test_calculate_checkout_line_unit_price_with_voucher_one_line(
    checkout_with_item, shipping_zone, address, voucher
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager()
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
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = _calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        channel,
        [],
        rate,
        prices_entered_with_tax,
    )

    # then
    currency = checkout_with_item.currency
    unit_gross = Money(total_price.amount - discount_amount, currency) / line.quantity
    assert quantize_price(line_price, line_price.currency) == TaxedMoney(
        net=quantize_price(unit_gross / Decimal(1.23), currency),
        gross=quantize_price(unit_gross, currency),
    )


def test_calculate_checkout_line_unit_price_with_voucher_multiple_lines(
    checkout_with_item, shipping_zone, address, voucher, product_list
):
    # given
    manager = get_plugins_manager()
    checkout = checkout_with_item

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout_info = fetch_checkout_info(checkout, [], [], manager)
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
    discount_amount = Decimal("5")
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
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = _calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        channel,
        [],
        rate,
        prices_entered_with_tax,
    )

    # then
    currency = checkout.currency
    discount_amount = quantize_price(
        total_line_price / total_unit_prices * discount_amount, currency
    )
    unit_gross = (total_line_price - Money(discount_amount, currency)) / line.quantity
    assert quantize_price(line_price, currency) == TaxedMoney(
        net=quantize_price(unit_gross / Decimal("1.23"), currency),
        gross=quantize_price(unit_gross, currency),
    )


def test_calculate_checkout_line_unit_price_with_voucher_multiple_lines_last_line(
    checkout_with_item, shipping_zone, address, voucher, product_list
):
    # given
    manager = get_plugins_manager()
    checkout = checkout_with_item

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    currency = checkout.currency

    checkout_info = fetch_checkout_info(checkout, [], [], manager)
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
    discount_amount = Decimal("5")
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
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_line_info = lines[-1]

    # when
    line_price = _calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        channel,
        [],
        rate,
        prices_entered_with_tax,
    )

    # then
    discount_amount = (
        discount_amount
        - (total_unit_prices - total_line_price) / total_unit_prices * discount_amount
    )
    unit_gross = (total_line_price - Money(discount_amount, currency)) / line.quantity
    assert quantize_price(line_price, currency) == TaxedMoney(
        net=quantize_price(unit_gross / Decimal("1.23"), currency),
        gross=quantize_price(unit_gross, currency),
    )


def test_calculate_checkout_line_unit_price_with_shipping_voucher(
    checkout_with_item,
    shipping_zone,
    address,
    voucher_shipping_type,
):
    # given
    manager = get_plugins_manager()
    checkout = checkout_with_item

    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    line = checkout.lines.first()

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.discount_amount = Decimal("5")
    checkout.voucher_code = voucher_shipping_type.code
    checkout.save()

    variant = line.variant
    product = variant.product
    product.tax_class.country_rates.update_or_create(country=address.country, rate=rate)

    channel = checkout.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    unit_gross = channel_listing.price

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = _calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        channel,
        [],
        rate,
        prices_entered_with_tax,
    )

    # then
    assert quantize_price(line_price, checkout.currency) == TaxedMoney(
        net=quantize_price(unit_gross / Decimal("1.23"), checkout.currency),
        gross=unit_gross,
    )


def test_calculate_checkout_shipping(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager()
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
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)

    # when
    shipping_price = calculate_checkout_shipping(
        checkout_info, lines, rate, prices_entered_with_tax
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


def test_calculate_checkout_shipping_no_shipping_price(
    checkout_with_item,
    discount_info,
    address,
    warehouse_for_cc,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager()
    rate = Decimal(23)
    prices_entered_with_tax = True
    _enable_flat_rates(checkout, prices_entered_with_tax)

    checkout.shipping_address = address
    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["shipping_address", "collection_point"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)

    # when
    shipping_price = calculate_checkout_shipping(
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
    discount_info,
    address,
    voucher_shipping_type,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager()
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
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)
    channel = checkout.channel
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    price = shipping_channel_listings.price

    # when
    shipping_price = calculate_checkout_shipping(
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
    discount_info,
    address,
    voucher_shipping_type,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager()
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
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)

    # when
    shipping_price = calculate_checkout_shipping(
        checkout_info, lines, rate, prices_entered_with_tax
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == zero_taxed_money(checkout.currency)


def test_calculate_checkout_shipping_free_entire_order_voucher(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    voucher,
):
    # given
    checkout = checkout_with_item
    manager = get_plugins_manager()
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
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)

    # when
    shipping_price = calculate_checkout_shipping(
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
