from decimal import Decimal
from urllib.parse import urlparse

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ....checkout import calculations
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import add_variant_to_checkout
from ....core.prices import quantize_price
from ....core.taxes import zero_taxed_money
from ....discount import DiscountValueType, OrderDiscountType
from ....product.models import Product
from ...manager import get_plugins_manager
from ...models import PluginConfiguration
from ...vatlayer import (
    DEFAULT_TAX_RATE_NAME,
    apply_tax_to_price,
    get_tax_rate_by_name,
    get_taxed_shipping_price,
    get_taxes_for_country,
)
from ..plugin import VatlayerPlugin


def get_url_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    return get_url_path(response["Location"])


@pytest.fixture
def compare_taxes():
    def fun(taxes_1, taxes_2):
        assert len(taxes_1) == len(taxes_2)

        for rate_name, tax in taxes_1.items():
            value_1 = tax["value"]
            value_2 = taxes_2.get(rate_name)["value"]
            assert value_1 == value_2

    return fun


def test_get_tax_rate_by_name(taxes):
    rate_name = "pharmaceuticals"
    tax_rate = get_tax_rate_by_name(rate_name, taxes)

    assert tax_rate == taxes[rate_name]["value"]


def test_get_tax_rate_by_name_fallback_to_standard(taxes):
    rate_name = "unexisting tax rate"
    tax_rate = get_tax_rate_by_name(rate_name, taxes)

    assert tax_rate == taxes[DEFAULT_TAX_RATE_NAME]["value"]


def test_get_tax_rate_by_name_empty_taxes(product):
    rate_name = "unexisting tax rate"
    tax_rate = get_tax_rate_by_name(rate_name)

    assert tax_rate == 0


@pytest.mark.parametrize(
    "price, charge_taxes, expected_price",
    [
        (
            Money(10, "USD"),
            False,
            TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD")),
        ),
        (
            Money(10, "USD"),
            True,
            TaxedMoney(net=Money("8.13", "USD"), gross=Money(10, "USD")),
        ),
    ],
)
def test_get_taxed_shipping_price(
    site_settings, vatlayer, price, charge_taxes, expected_price
):
    site_settings.charge_taxes_on_shipping = charge_taxes
    site_settings.save()

    shipping_price = get_taxed_shipping_price(price, taxes=vatlayer)

    assert shipping_price == expected_price


def test_get_taxes_for_country(vatlayer, compare_taxes):
    taxes = get_taxes_for_country(Country("PL"))
    compare_taxes(taxes, vatlayer)


def test_apply_tax_to_price_do_not_include_tax(site_settings, taxes):
    site_settings.include_taxes_in_prices = False
    site_settings.save()

    money = Money(100, "USD")
    assert apply_tax_to_price(taxes, "standard", money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(123, "USD")
    )
    assert apply_tax_to_price(taxes, "medical", money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(108, "USD")
    )

    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))
    assert apply_tax_to_price(taxes, "standard", taxed_money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(123, "USD")
    )
    assert apply_tax_to_price(taxes, "medical", taxed_money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(108, "USD")
    )


def test_apply_tax_to_price_do_not_include_tax_fallback_to_standard_rate(
    site_settings, taxes
):
    site_settings.include_taxes_in_prices = False
    site_settings.save()

    money = Money(100, "USD")
    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(123, "USD"))
    assert apply_tax_to_price(taxes, "space suits", money) == taxed_money


def test_apply_tax_to_price_include_tax(taxes):
    money = Money(100, "USD")
    assert apply_tax_to_price(taxes, "standard", money) == TaxedMoney(
        net=Money("81.30", "USD"), gross=Money(100, "USD")
    )
    assert apply_tax_to_price(taxes, "medical", money) == TaxedMoney(
        net=Money("92.59", "USD"), gross=Money(100, "USD")
    )


def test_apply_tax_to_price_include_fallback_to_standard_rate(taxes):
    money = Money(100, "USD")
    assert apply_tax_to_price(taxes, "space suits", money) == TaxedMoney(
        net=Money("81.30", "USD"), gross=Money(100, "USD")
    )

    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))
    assert apply_tax_to_price(taxes, "space suits", taxed_money) == TaxedMoney(
        net=Money("81.30", "USD"), gross=Money(100, "USD")
    )


def test_apply_tax_to_price_raise_typeerror_for_invalid_type(taxes):
    with pytest.raises(TypeError):
        assert apply_tax_to_price(taxes, "standard", 100)


def test_apply_tax_to_price_no_taxes_return_taxed_money():
    money = Money(100, "USD")
    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))

    assert apply_tax_to_price(None, "standard", money) == taxed_money
    assert apply_tax_to_price(None, "medical", taxed_money) == taxed_money


def test_apply_tax_to_price_no_taxes_return_taxed_money_range():
    money_range = MoneyRange(Money(100, "USD"), Money(200, "USD"))
    taxed_money_range = TaxedMoneyRange(
        TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD")),
        TaxedMoney(net=Money(200, "USD"), gross=Money(200, "USD")),
    )

    assert apply_tax_to_price(None, "standard", money_range) == taxed_money_range
    assert apply_tax_to_price(None, "standard", taxed_money_range) == taxed_money_range


def test_apply_tax_to_price_no_taxes_raise_typeerror_for_invalid_type():
    with pytest.raises(TypeError):
        assert apply_tax_to_price(None, "standard", 100)


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, taxes_in_prices",
    [
        (True, "20.34", "25.00", "0.0", True),
        (True, "20.00", "24.60", "5.0", False),
        (False, "40.00", "49.20", "0.0", False),
        (False, "30.09", "37.00", "3.0", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_total(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    voucher,
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
):
    # given
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.discount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    discounts = [discount_info] if with_discount else None
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, address, discounts)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, taxes_in_prices",
    [
        (True, "20.34", "25.00", "0.0", True),
        (True, "20.00", "24.60", "5.0", False),
        (False, "40.00", "49.20", "0.0", False),
        (False, "30.08", "37.00", "3.0", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_total_shipping_voucher(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    voucher_shipping_type,
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
):
    # given
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.voucher_code = voucher_shipping_type.code
    checkout_with_item.discount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    discounts = [discount_info] if with_discount else None
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, address, discounts)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_checkout_total_from_origin_country(
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
):
    plugin = vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    plugin.assign_tax_code_to_object_meta(product, "standard", None)
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    total = manager.calculate_checkout_total(
        checkout_info, lines, address, [discount_info]
    )
    total = quantize_price(total, total.currency)

    # make sure that address has PL code
    assert address.country.code == "PL"

    # make sure that we applied DE taxes (19%)
    assert total == TaxedMoney(net=Money("21.00", "USD"), gross=Money("25.00", "USD"))


def test_calculate_checkout_total_with_excluded_country(
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
):
    plugin = vatlayer_plugin(origin_country="PL", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    plugin.assign_tax_code_to_object_meta(product, "standard", None)
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    total = manager.calculate_checkout_total(
        checkout_info, lines, address, [discount_info]
    )
    total = quantize_price(total, total.currency)

    # make sure that we not have VAT
    assert total == TaxedMoney(net=Money("25.00", "USD"), gross=Money("25.00", "USD"))


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (True, "20.35", "25.00", True),
        (False, "40.65", "50.00", True),
        (True, "25.00", "30.75", False),
        (False, "50.00", "61.50", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_subtotal(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    stock,
):
    variant = stock.product_variant
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    manager = get_plugins_manager()

    product = variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    discounts = [discount_info] if with_discount else None
    checkout_info = fetch_checkout_info(checkout_with_item, [], discounts, manager)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_checkout_subtotal_from_origin_country(
    site_settings,
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
):
    plugin = vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    plugin.assign_tax_code_to_object_meta(product, "standard", None)
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    total = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, [discount_info]
    )
    total = quantize_price(total, total.currency)

    # make sure that address has PL code
    assert address.country.code == "PL"

    # make sure that we applied DE taxes (19%)
    assert total == TaxedMoney(net=Money("12.60", "USD"), gross=Money("15.00", "USD"))


def test_calculate_checkout_subtotal_with_excluded_country(
    site_settings,
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
):
    plugin = vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    plugin.assign_tax_code_to_object_meta(product, "standard", None)
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    total = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, [discount_info]
    )
    total = quantize_price(total, total.currency)

    # make sure that we not have VAT
    assert total == TaxedMoney(net=Money("15.00", "USD"), gross=Money("15.00", "USD"))


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_order_shipping(vatlayer, order_line, shipping_zone, site_settings):
    manager = get_plugins_manager()
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()
    price = manager.calculate_order_shipping(order)
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


def test_calculate_order_shipping_from_origin_country(
    vatlayer_plugin, order_line, shipping_zone, site_settings
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    price = manager.calculate_order_shipping(order)
    price = quantize_price(price, price.currency)

    # make sure that address has PL code
    assert order.shipping_address.country.code == "PL"

    # make sure that we applied DE taxes (19%)
    assert price == TaxedMoney(net=Money("8.40", "USD"), gross=Money("10.00", "USD"))


def test_calculate_order_shipping_with_excluded_country(
    vatlayer_plugin, order_line, shipping_zone, site_settings
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    price = manager.calculate_order_shipping(order)
    price = quantize_price(price, price.currency)

    assert price == TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_order_shipping_for_order_without_shipping(
    vatlayer, order_line, shipping_zone, site_settings
):
    manager = get_plugins_manager()
    order = order_line.order
    order.shipping_method = None
    order.save()
    price = manager.calculate_order_shipping(order)
    assert price == zero_taxed_money(order.currency)


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_order_shipping_voucher_on_shipping(
    vatlayer, order_line, shipping_zone, voucher_shipping_type
):
    # given
    manager = get_plugins_manager()
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.voucher = voucher_shipping_type
    order.save()

    currency = order.currency
    discount_amount = Decimal("5.0")
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=discount_amount,
    )
    channel = order.channel
    shipping_channel_listings = method.channel_listings.get(channel=channel)
    shipping_price = shipping_channel_listings.price

    # when
    price = manager.calculate_order_shipping(order)

    # then
    price = quantize_price(price, price.currency)
    expected_gross_amount = shipping_price.amount - discount_amount
    assert price == TaxedMoney(
        net=quantize_price(
            Money(expected_gross_amount / Decimal("1.23"), currency), currency
        ),
        gross=Money(expected_gross_amount, currency),
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_order_shipping_free_shipping_voucher(
    vatlayer, order_line, shipping_zone, voucher_shipping_type
):
    # given
    manager = get_plugins_manager()
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.voucher = voucher_shipping_type
    order.save()

    currency = order.currency
    channel = order.channel
    shipping_channel_listings = method.channel_listings.get(channel=channel)
    shipping_price = shipping_channel_listings.price

    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("100.0"),
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=shipping_price.amount,
    )

    # when
    price = manager.calculate_order_shipping(order)

    # then
    price = quantize_price(price, price.currency)
    assert price == zero_taxed_money(currency)


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_line_total(
    vatlayer, checkout_with_item, shipping_zone, address, site_settings
):
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()
    assert line.quantity > 1

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    checkout_with_item.save()

    variant = line.variant
    product = variant.product
    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    assert line_price == TaxedMoney(
        net=Money("8.13", "USD") * line.quantity,
        gross=Money("10.00", "USD") * line.quantity,
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_line_total_voucher_on_entire_order(
    vatlayer, checkout_with_item, shipping_zone, address, voucher
):
    # given
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()
    assert line.quantity > 1

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    discount_amount = Decimal("5")
    checkout_with_item.discount_amount = discount_amount
    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.save()

    variant = line.variant
    product = variant.product
    channel = checkout_with_item.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_price = channel_listing.price * line.quantity

    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    # then
    currency = checkout_with_item.currency
    total_gross = Money(total_price.amount - discount_amount, currency)
    unit_net = quantize_price(total_gross / line.quantity / Decimal("1.23"), currency)
    assert line_price == TaxedMoney(
        net=quantize_price(unit_net * line.quantity, currency),
        gross=quantize_price(total_gross, currency),
    )


def test_calculate_checkout_line_total_from_origin_country(
    vatlayer_plugin, checkout_with_item, shipping_zone, address, site_settings
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()
    assert line.quantity > 1

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    checkout_with_item.save()

    variant = line.variant
    product = variant.product
    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    # make sure that we applied DE taxes (19%)
    assert line_price == TaxedMoney(
        net=Money("8.40", "USD") * line.quantity,
        gross=Money("10.00", "USD") * line.quantity,
    )


def test_calculate_checkout_line_total_with_excluded_country(
    vatlayer_plugin, checkout_with_item, shipping_zone, address, site_settings
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()
    assert line.quantity > 1

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    checkout_with_item.save()

    variant = line.variant
    product = variant.product
    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    assert line_price == TaxedMoney(
        net=Money("10.00", "USD") * line.quantity,
        gross=Money("10.00", "USD") * line.quantity,
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_update_taxes_for_order_lines(vatlayer, order_with_lines):
    # given
    currency = order_with_lines.currency
    manager = get_plugins_manager()

    # when
    lines = manager.update_taxes_for_order_lines(
        order_with_lines, list(order_with_lines.lines.all())
    )

    # then
    for line in lines:
        assert line.unit_price == TaxedMoney(
            net=quantize_price(line.base_unit_price / Decimal("1.23"), currency),
            gross=line.base_unit_price,
        )
        assert line.undiscounted_unit_price == line.unit_price
        assert line.total_price == TaxedMoney(
            net=quantize_price(
                line.base_unit_price / Decimal("1.23") * line.quantity, currency
            ),
            gross=line.base_unit_price * line.quantity,
        )
        assert line.undiscounted_total_price == line.total_price
        assert line.tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_update_taxes_for_order_lines_voucher_on_entire_order(
    vatlayer, order_with_lines, voucher
):
    # given
    order = order_with_lines
    currency = order.currency
    manager = get_plugins_manager()

    order.voucher = voucher
    lines = list(order.lines.all())
    total_amount = sum([line.base_unit_price.amount * line.quantity for line in lines])
    order.undiscounted_total_gross_amount = total_amount
    order.undiscounted_total_net_amount = total_amount
    order.save(
        update_fields=[
            "voucher",
            "undiscounted_total_gross_amount",
            "undiscounted_total_net_amount",
        ]
    )

    order_discount_amount = Decimal("5.0")
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name=voucher.code,
        currency=currency,
        amount_value=order_discount_amount,
    )

    # when
    lines = manager.update_taxes_for_order_lines(order, lines)

    # then
    for line in lines:
        total_line_price = line.base_unit_price * line.quantity
        discount_amount = quantize_price(
            total_line_price.amount / total_amount * order_discount_amount, currency
        )
        unit_gross = (
            total_line_price - Money(discount_amount, currency)
        ) / line.quantity
        assert line.unit_price == TaxedMoney(
            net=quantize_price(unit_gross / Decimal("1.23"), currency),
            gross=quantize_price(unit_gross, currency),
        )
        assert line.undiscounted_unit_price == TaxedMoney(
            net=quantize_price(line.base_unit_price / Decimal("1.23"), currency),
            gross=line.base_unit_price,
        )
        assert line.total_price == TaxedMoney(
            net=quantize_price(unit_gross / Decimal("1.23"), currency) * line.quantity,
            gross=quantize_price(unit_gross, currency) * line.quantity,
        )
        assert line.undiscounted_total_price == TaxedMoney(
            net=quantize_price(line.base_unit_price / Decimal("1.23"), currency)
            * line.quantity,
            gross=quantize_price(line.base_unit_price * line.quantity, currency),
        )
        assert line.tax_rate == (line.unit_price.tax / line.unit_price.net).quantize(
            Decimal(".0001")
        )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_update_taxes_for_order_lines_voucher_on_shipping(
    vatlayer, order_with_lines, voucher_shipping_type
):
    # given
    order = order_with_lines
    currency = order_with_lines.currency
    manager = get_plugins_manager()

    order.voucher = voucher_shipping_type
    lines = list(order.lines.all())
    total_amount = sum([line.base_unit_price.amount * line.quantity for line in lines])
    order.undiscounted_total_gross_amount = total_amount
    order.undiscounted_total_net_amount = total_amount
    order.save(
        update_fields=[
            "voucher",
            "undiscounted_total_gross_amount",
            "undiscounted_total_net_amount",
        ]
    )

    order_discount_amount = Decimal("5.0")
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=order_discount_amount,
    )

    # when
    lines = manager.update_taxes_for_order_lines(
        order_with_lines, list(order_with_lines.lines.all())
    )

    # then
    for line in lines:
        assert line.unit_price == TaxedMoney(
            net=quantize_price(line.base_unit_price / Decimal("1.23"), currency),
            gross=line.base_unit_price,
        )
        assert line.undiscounted_unit_price == line.unit_price
        assert line.total_price == TaxedMoney(
            net=quantize_price(
                line.base_unit_price / Decimal("1.23") * line.quantity, currency
            ),
            gross=line.base_unit_price * line.quantity,
        )
        assert line.undiscounted_total_price == line.total_price
        assert line.tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_line_unit_price(
    vatlayer, checkout_with_item, shipping_zone, address, site_settings
):
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    checkout_with_item.save()

    variant = line.variant
    product = variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    assert line_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_line_unit_price_with_voucher_one_line(
    vatlayer, checkout_with_item, shipping_zone, address, voucher, site_settings
):
    # given
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    discount_amount = Decimal("5")
    checkout_with_item.discount_amount = discount_amount
    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.save()

    variant = line.variant
    product = variant.product
    channel = checkout_with_item.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_price = channel_listing.price * line.quantity
    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    # then
    currency = checkout_with_item.currency
    unit_gross = Money(total_price.amount - discount_amount, currency) / line.quantity
    assert line_price == TaxedMoney(
        net=quantize_price(unit_gross / Decimal("1.23"), currency),
        gross=quantize_price(unit_gross, currency),
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_line_unit_price_with_voucher_multiple_lines(
    vatlayer, checkout_with_item, shipping_zone, address, voucher, product_list
):
    # given
    manager = get_plugins_manager()

    checkout_with_item
    checkout_info = fetch_checkout_info(checkout_with_item, [], [], manager)
    variant_1 = product_list[0].variants.last()
    variant_2 = product_list[1].variants.last()
    qty_1 = 2
    qty_2 = 3
    add_variant_to_checkout(checkout_info, variant_1, qty_1)
    add_variant_to_checkout(checkout_info, variant_2, qty_2)

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    discount_amount = Decimal("5")
    checkout_with_item.discount_amount = discount_amount
    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    variant = line.variant
    product = variant.product
    channel = checkout_with_item.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_line_price = channel_listing.price * line.quantity
    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    total_unit_prices = (
        variant_1.channel_listings.get(channel=channel).price * qty_1
        + variant_2.channel_listings.get(channel=channel).price * qty_2
        + total_line_price
    )

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    # then
    currency = checkout_with_item.currency
    discount_amount = quantize_price(
        total_line_price / total_unit_prices * discount_amount, currency
    )
    unit_gross = (total_line_price - Money(discount_amount, currency)) / line.quantity
    assert line_price == TaxedMoney(
        net=quantize_price(unit_gross / Decimal("1.23"), currency),
        gross=quantize_price(unit_gross, currency),
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_line_unit_price_with_voucher_multiple_lines_last_line(
    vatlayer, checkout_with_item, shipping_zone, address, voucher, product_list
):
    # given
    manager = get_plugins_manager()
    currency = checkout_with_item.currency

    checkout_info = fetch_checkout_info(checkout_with_item, [], [], manager)
    variant_1 = product_list[0].variants.last()
    variant_2 = product_list[1].variants.last()
    qty_1 = 2
    qty_2 = 3
    add_variant_to_checkout(checkout_info, variant_1, qty_1)
    add_variant_to_checkout(checkout_info, variant_2, qty_2)

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    discount_amount = Decimal("5")
    checkout_with_item.discount_amount = discount_amount
    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.save()

    line = checkout_with_item.lines.last()
    variant = line.variant
    product = variant.product
    channel = checkout_with_item.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    total_line_price = channel_listing.price * line.quantity
    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    total_unit_prices = Money(
        sum(
            [
                line.variant.channel_listings.get(channel=channel).price.amount
                * line.quantity
                for line in checkout_with_item.lines.all()
            ]
        ),
        currency,
    )

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[-1]

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    # then
    discount_amount = (
        discount_amount
        - (total_unit_prices - total_line_price) / total_unit_prices * discount_amount
    )
    unit_gross = (total_line_price - Money(discount_amount, currency)) / line.quantity
    assert line_price == TaxedMoney(
        net=quantize_price(unit_gross / Decimal("1.23"), currency),
        gross=quantize_price(unit_gross, currency),
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_line_unit_price_with_shipping_voucher(
    vatlayer,
    checkout_with_item,
    shipping_zone,
    address,
    voucher_shipping_type,
    site_settings,
):
    # given
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()

    method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method_name = method.name
    checkout_with_item.shipping_method = method
    checkout_with_item.discount_amount = Decimal("5")
    checkout_with_item.voucher_code = voucher_shipping_type.code
    checkout_with_item.save()

    variant = line.variant
    product = variant.product
    channel = checkout_with_item.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    unit_gross = channel_listing.price
    manager.assign_tax_code_to_object_meta(variant.product, "standard")
    product.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
    )

    # then
    assert line_price == TaxedMoney(
        net=quantize_price(unit_gross / Decimal("1.23"), checkout_with_item.currency),
        gross=unit_gross,
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_tax_rate_percentage_value(
    vatlayer, order_line, shipping_zone, site_settings, product
):
    manager = get_plugins_manager()
    country = Country("PL")
    tax_rate = manager.get_tax_rate_percentage_value(product, country)
    assert tax_rate == Decimal("23")


def test_get_tax_rate_percentage_value_from_origin_country(
    vatlayer_plugin, order_line, shipping_zone, site_settings, product
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    country = Country("PL")
    tax_rate = manager.get_tax_rate_percentage_value(product, country)
    # make sure that we return DE tax rate
    assert tax_rate == Decimal("19")


def test_get_tax_rate_percentage_value_with_excluded_country(
    vatlayer_plugin, order_line, shipping_zone, site_settings, product
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    country = Country("PL")
    tax_rate = manager.get_tax_rate_percentage_value(product, country)

    assert tax_rate == Decimal("0")


def test_save_plugin_configuration(vatlayer, settings, channel_USD):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    manager.save_plugin_configuration(
        VatlayerPlugin.PLUGIN_ID, channel_USD.slug, {"active": False}
    )

    configuration = PluginConfiguration.objects.get(identifier=VatlayerPlugin.PLUGIN_ID)
    assert not configuration.active


def test_save_plugin_configuration_cannot_be_enabled_without_config(
    settings, channel_USD
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    with pytest.raises(ValidationError):
        manager.save_plugin_configuration(
            VatlayerPlugin.PLUGIN_ID,
            channel_USD.slug,
            {"active": True},
        )


def test_show_taxes_on_storefront(vatlayer, settings):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    assert manager.show_taxes_on_storefront() is True


def test_get_tax_rate_type_choices(vatlayer, settings, monkeypatch):
    expected_choices = [
        "accommodation",
        "admission to cultural events",
        "admission to entertainment events",
    ]
    monkeypatch.setattr(
        "saleor.plugins.vatlayer.plugin.get_tax_rate_types",
        lambda: expected_choices,
    )
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    choices = manager.get_tax_rate_type_choices()

    # add a default choice
    expected_choices.append("standard")

    assert len(choices) == 4
    for choice in choices:
        assert choice.code in expected_choices


def test_apply_taxes_to_product(
    vatlayer, settings, variant, discount_info, channel_USD
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    country = Country("PL")
    manager = get_plugins_manager()
    variant.product.metadata = {
        "vatlayer.code": "standard",
        "vatlayer.description": "standard",
    }
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    price = manager.apply_taxes_to_product(
        variant.product,
        variant.get_price(
            variant.product, [], channel_USD, variant_channel_listing, [discount_info]
        ),
        country,
        channel_USD.slug,
    )
    assert price == TaxedMoney(net=Money("4.07", "USD"), gross=Money("5.00", "USD"))


def test_apply_taxes_to_product_from_origin_country(
    vatlayer_plugin, settings, variant, discount_info, channel_USD
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    country = Country("PL")

    variant.product.metadata = {
        "vatlayer.code": "standard",
        "vatlayer.description": "standard",
    }
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)

    price = manager.apply_taxes_to_product(
        variant.product,
        variant.get_price(
            variant.product, [], channel_USD, variant_channel_listing, [discount_info]
        ),
        country,
        channel_USD.slug,
    )

    assert price == TaxedMoney(net=Money("4.20", "USD"), gross=Money("5.00", "USD"))


def test_apply_taxes_to_product_with_excluded_country(
    vatlayer_plugin, settings, variant, discount_info, channel_USD
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    country = Country("PL")

    variant.product.metadata = {
        "vatlayer.code": "standard",
        "vatlayer.description": "standard",
    }
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)

    price = manager.apply_taxes_to_product(
        variant.product,
        variant.get_price(
            variant.product, [], channel_USD, variant_channel_listing, [discount_info]
        ),
        country,
        channel_USD.slug,
    )

    assert price == TaxedMoney(net=Money("5.00", "USD"), gross=Money("5.00", "USD"))


def test_apply_taxes_to_product_uses_taxes_from_product_type(
    vatlayer, settings, variant, discount_info, channel_USD
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    country = Country("PL")
    manager = get_plugins_manager()
    product = variant.product
    product.metadata = {}
    product.product_type.metadata = {
        "vatlayer.code": "standard",
        "vatlayer.description": "standard",
    }
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    price = manager.apply_taxes_to_product(
        product,
        variant.get_price(
            product, [], channel_USD, variant_channel_listing, [discount_info]
        ),
        country,
        channel_USD.slug,
    )
    assert price == TaxedMoney(net=Money("4.07", "USD"), gross=Money("5.00", "USD"))


def test_calculations_checkout_total_with_vatlayer(
    vatlayer, settings, checkout_with_item
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_subtotal = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert checkout_subtotal == TaxedMoney(
        net=Money("30", "USD"), gross=Money("30", "USD")
    )


def test_calculations_checkout_subtotal_with_vatlayer(
    vatlayer, settings, checkout_with_item
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert checkout_subtotal == TaxedMoney(
        net=Money("30", "USD"), gross=Money("30", "USD")
    )


def test_calculations_checkout_shipping_price_with_vatlayer(
    vatlayer, settings, checkout_with_item
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert checkout_shipping_price == TaxedMoney(
        net=Money("0", "USD"), gross=Money("0", "USD")
    )


def test_skip_diabled_plugin(settings, channel_USD):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    plugin: VatlayerPlugin = manager.get_plugin(
        VatlayerPlugin.PLUGIN_ID, channel_USD.slug
    )

    assert (
        plugin._skip_plugin(
            previous_value=TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
        )
        is True
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_checkout_line_tax_rate(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
):
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.230")


def test_get_checkout_line_tax_rate_from_origin_country(
    site_settings,
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.190")


def test_get_checkout_line_tax_rate_with_excluded_country(
    site_settings,
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(15, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_checkout_line_tax_rate_order_not_valid(
    site_settings,
    vatlayer,
    checkout_with_item,
):
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.25")


def test_get_order_line_tax_rate_from_origin_country(
    site_settings,
    vatlayer_plugin,
    order_line,
    address,
    shipping_zone,
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_line_tax_rate(
        order, product, order_line.variant, address, unit_price
    )
    assert tax_rate == Decimal("0.190")


def test_get_order_line_tax_rate_with_excluded_country(
    site_settings,
    vatlayer_plugin,
    order_line,
    address,
    shipping_zone,
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(15, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_line_tax_rate(
        order, product, order_line.variant, address, unit_price
    )
    assert tax_rate == Decimal("0")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_order_line_tax_rate(
    site_settings,
    vatlayer,
    order_line,
    address,
    shipping_zone,
):
    manager = get_plugins_manager()
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_line_tax_rate(
        order, product, order_line.variant, address, unit_price
    )
    assert tax_rate == Decimal("0.230")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_order_line_tax_rate_order_no_address_given(
    site_settings,
    order_line,
    vatlayer,
):
    manager = get_plugins_manager()
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_line_tax_rate(
        order, product, order_line.variant, None, unit_price
    )
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_checkout_shipping_tax_rate(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
):
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.230")


def test_get_checkout_shipping_tax_rate_from_origin_country(
    site_settings,
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.190")


def test_get_checkout_shipping_tax_rate_with_excluded_country(
    site_settings,
    vatlayer_plugin,
    checkout_with_item,
    address,
    shipping_zone,
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(15, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_checkout_shipping_tax_rate_no_address(
    site_settings,
    vatlayer,
    checkout_with_item,
):
    manager = get_plugins_manager()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_checkout_shipping_tax_rate_skip_plugin(
    site_settings, vatlayer, checkout_with_item, monkeypatch, address, shipping_zone
):
    manager = get_plugins_manager()
    monkeypatch.setattr(
        "saleor.plugins.vatlayer.plugin.VatlayerPlugin._skip_plugin",
        lambda *_: True,
    )

    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_order_shipping_tax_rate(
    site_settings,
    vatlayer,
    order_line,
    address,
    shipping_zone,
):
    manager = get_plugins_manager()
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0.230")


def test_get_order_shipping_tax_rate_from_origin_country(
    site_settings,
    vatlayer_plugin,
    order_line,
    address,
    shipping_zone,
):
    vatlayer_plugin(
        origin_country="DE", countries_to_calculate_taxes_from_origin="PL,FR"
    )
    manager = get_plugins_manager()

    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0.190")


def test_get_order_shipping_tax_rate_with_excluded_country(
    site_settings,
    vatlayer_plugin,
    order_line,
    address,
    shipping_zone,
):
    vatlayer_plugin(origin_country="DE", excluded_countries="PL,FR")
    manager = get_plugins_manager()

    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(15, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_order_shipping_tax_rate_no_address_given(
    site_settings,
    order_line,
    vatlayer,
):
    manager = get_plugins_manager()
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    order.shipping_address = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "billing_address"])

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_order_shipping_tax_rate_skip_plugin(
    site_settings, order_line, vatlayer, monkeypatch
):
    manager = get_plugins_manager()
    monkeypatch.setattr(
        "saleor.plugins.vatlayer.plugin.VatlayerPlugin._skip_plugin",
        lambda *_: True,
    )
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_shipping(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    site_settings,
    vatlayer,
):
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, [discount_info]
    )
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_shipping_no_shipping_price(
    checkout_with_item,
    discount_info,
    address,
    warehouse_for_cc,
    vatlayer,
):
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.collection_point = warehouse_for_cc
    checkout_with_item.save(update_fields=["shipping_address", "collection_point"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, [discount_info]
    )
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("0.00", "USD"), gross=Money("0.00", "USD")
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_shipping_voucher_on_shipping(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    voucher_shipping_type,
    site_settings,
    vatlayer,
):
    # given
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_shipping_type.code
    discount_amount = Decimal("5.0")
    checkout_with_item.discount_amount = discount_amount
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    channel = checkout_with_item.channel
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    price = shipping_channel_listings.price

    # when
    shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, [discount_info]
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    currency = checkout_with_item.currency
    expected_gross_shipping_price = Money(price.amount - discount_amount, currency)
    assert shipping_price == TaxedMoney(
        net=quantize_price(expected_gross_shipping_price / Decimal(1.23), currency),
        gross=expected_gross_shipping_price,
    )


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_shipping_free_shipping_voucher(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    voucher_shipping_type,
    site_settings,
    vatlayer,
):
    # given
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_shipping_type.code
    channel = checkout_with_item.channel
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    price = shipping_channel_listings.price
    checkout_with_item.discount_amount = price.amount
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )

    # when
    shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, [discount_info]
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == zero_taxed_money(checkout_with_item.currency)


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_calculate_checkout_shipping_free_entire_order_voucher(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    voucher,
    site_settings,
    vatlayer,
):
    # given
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher.code
    channel = checkout_with_item.channel
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    discount_amount = Decimal("5.0")
    checkout_with_item.discount_amount = discount_amount
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )

    # when
    shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, [discount_info]
    )

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert (
        shipping_price
        == shipping_price
        == TaxedMoney(
            net=quantize_price(
                shipping_channel_listings.price / Decimal(1.23),
                checkout_with_item.currency,
            ),
            gross=shipping_channel_listings.price,
        )
    )
