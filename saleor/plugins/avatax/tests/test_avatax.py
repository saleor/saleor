import datetime
from decimal import Decimal
from json import JSONDecodeError
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from prices import Money, TaxedMoney
from requests import RequestException

from ....checkout.fetch import (
    CheckoutInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
    get_valid_shipping_method_list_for_checkout_info,
)
from ....checkout.utils import add_variant_to_checkout
from ....core.prices import quantize_price
from ....core.taxes import TaxError, TaxType
from ....product.models import Product, ProductType
from ...manager import get_plugins_manager
from ...models import PluginConfiguration
from .. import (
    META_CODE_KEY,
    META_DESCRIPTION_KEY,
    AvataxConfiguration,
    TransactionType,
    _validate_adddress_details,
    api_get_request,
    api_post_request,
    generate_request_data_from_checkout,
    get_cached_tax_codes_or_fetch,
    get_order_request_data,
    get_order_tax_data,
    taxes_need_new_fetch,
)
from ..plugin import AvataxPlugin


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (True, "12.20", "15.00", True),
        (False, "24.39", "30.00", True),
        (True, "15.00", "18.45", False),
        (False, "30.00", "36.90", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total(
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    discount_info,
    checkout_with_item,
    address,
    ship_to_pl_address,
    site_settings,
    monkeypatch,
    shipping_zone,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    site_settings.company_address = address
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}
    product.charge_taxes = True
    product.save()
    product.product_type.save()
    discounts = [discount_info] if with_discount else None

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)
    checkout_line_info = lines[0]

    total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        discounts,
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr()
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_total(
    order_line,
    address,
    ship_to_pl_address,
    shipping_zone,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager()

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    order = order_line.order
    order.shipping_address = ship_to_pl_address
    order.shipping_method = shipping_zone.shipping_methods.get()
    order.save(update_fields=["shipping_address", "shipping_method"])

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.charge_taxes = True
    product.save()
    product.product_type.save()

    channel = order_line.order.channel
    channel_listing = variant.channel_listings.get(channel=channel)

    net = variant.get_price(product, [], channel, channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.unit_price = unit_price
    total_price = unit_price * order_line.quantity
    order_line.total_price = total_price
    order_line.save()

    total = manager.calculate_order_line_total(
        order_line.order,
        order_line,
        variant,
        product,
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(net=Money("30.00", "USD"), gross=Money("36.90", "USD"))


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_total_order_not_valid(
    order_line,
    address,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager()

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.charge_taxes = True
    product.save()
    product.product_type.save()

    order = order_line.order
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)

    net = variant.get_price(product, [], channel, channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.unit_price = unit_price
    total_price = unit_price * order_line.quantity
    order_line.total_price = total_price
    order_line.save()

    total = manager.calculate_order_line_total(
        order_line.order,
        order_line,
        variant,
        product,
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(net=Money("0.00", "USD"), gross=Money("0.00", "USD"))


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, taxes_in_prices",
    [
        (True, "22.32", "26.99", "0.0", True),
        (True, "21.99", "27.74", "5.0", False),
        (False, "41.99", "51.19", "0.0", False),
        (False, "31.51", "38.99", "3.0", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_uses_default_calculation(
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
    checkout_with_item,
    product_with_single_variant,
    discount_info,
    shipping_zone,
    address,
    ship_to_pl_address,
    site_settings,
    monkeypatch,
    plugin_configuration,
    non_default_category,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.save()
    site_settings.company_address = address
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}
    manager.assign_tax_code_to_object_meta(product.product_type, "PC040156")
    product.save()
    product.product_type.save()
    product_with_single_variant.charge_taxes = False
    product_with_single_variant.category = non_default_category
    product_with_single_variant.save()
    discounts = [discount_info] if with_discount else None
    checkout_info = fetch_checkout_info(checkout_with_item, [], discounts, manager)
    add_variant_to_checkout(checkout_info, product_with_single_variant.variants.get())
    lines = fetch_checkout_lines(checkout_with_item)

    total = manager.calculate_checkout_total(checkout_info, lines, address, discounts)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, taxes_in_prices",
    [
        (True, "23.94", "28.98", "0.0", True),
        (True, "23.98", "30.19", "5.0", False),
        (False, "43.98", "53.64", "0.0", False),
        (False, "33.13", "40.98", "3.0", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total(
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
    checkout_with_item,
    product_with_single_variant,
    discount_info,
    shipping_zone,
    address,
    ship_to_pl_address,
    site_settings,
    monkeypatch,
    plugin_configuration,
    non_default_category,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.save()
    site_settings.company_address = address
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}
    manager.assign_tax_code_to_object_meta(product.product_type, "PS081282")
    product.save()
    product.product_type.save()

    product_with_single_variant.charge_taxes = False
    product_with_single_variant.category = non_default_category
    product_with_single_variant.save()
    discounts = [discount_info] if with_discount else None
    checkout_info = fetch_checkout_info(checkout_with_item, [], discounts, manager)
    add_variant_to_checkout(checkout_info, product_with_single_variant.variants.get())
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(
        checkout_info, lines, ship_to_pl_address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_not_charged_product_and_shipping_with_0_price(
    checkout_with_item,
    shipping_zone,
    address,
    ship_to_pl_address,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.save()
    site_settings.company_address = address
    site_settings.include_taxes_in_prices = True
    site_settings.save()

    channel = checkout_with_item.channel
    shipping_method = shipping_zone.shipping_methods.get()
    shipping_channel_listing = shipping_method.channel_listings.get(channel=channel)
    shipping_channel_listing.price = Money(0, "USD")
    shipping_channel_listing.save()

    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    variant = line.variant
    product = variant.product
    product.charge_taxes = False
    product.metadata = {}
    manager.assign_tax_code_to_object_meta(product.product_type, "PS081282")
    product.save()
    product.product_type.save()

    discounts = None
    checkout_info = fetch_checkout_info(checkout_with_item, [], discounts, manager)
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(
        checkout_info, lines, ship_to_pl_address, discounts
    )
    total = quantize_price(total, total.currency)

    channel_listing = variant.channel_listings.get(channel=channel)
    expected_amount = (line.quantity * channel_listing.price).amount
    assert total == TaxedMoney(
        net=Money(expected_amount, "USD"), gross=Money(expected_amount, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_shipping(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    ship_to_pl_address,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager()
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines = fetch_checkout_lines(checkout_with_item)
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


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (True, "25.00", "30.75", False),
        (False, "40.65", "50.00", True),
        (False, "50.00", "61.50", False),
        (True, "20.33", "25.00", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_subtotal(
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    discount_info,
    checkout_with_item,
    stock,
    monkeypatch,
    site_settings,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    plugin_configuration()
    variant = stock.product_variant
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager()
    site_settings.company_address = address
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    discounts = [discount_info] if with_discount else None

    checkout_info = fetch_checkout_info(checkout_with_item, [], discounts, manager)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_subtotal_for_product_without_tax(
    checkout,
    stock,
    monkeypatch,
    site_settings,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    plugin_configuration()
    variant = stock.product_variant
    product = variant.product
    product.charge_taxes = False
    product.save(update_fields=["charge_taxes"])

    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager()
    site_settings.company_address = address
    site_settings.include_taxes_in_prices = True
    site_settings.save()

    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    quantity = 2
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    add_variant_to_checkout(checkout_info, variant, quantity)

    lines = fetch_checkout_lines(checkout)
    assert len(lines) == 1
    valid_methods = get_valid_shipping_method_list_for_checkout_info(
        checkout_info, ship_to_pl_address, lines, [], manager
    )
    checkout_info.valid_shipping_methods = valid_methods

    total = manager.calculate_checkout_subtotal(checkout_info, lines, address, [])
    total = quantize_price(total, total.currency)
    expected_total = variant.channel_listings.first().price_amount * quantity
    assert total == TaxedMoney(
        net=Money(expected_total, "USD"), gross=Money(expected_total, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping(
    order_line, shipping_zone, site_settings, address, plugin_configuration
):
    plugin_configuration()
    manager = get_plugins_manager()
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    site_settings.company_address = address
    site_settings.save()

    price = manager.calculate_order_shipping(order)
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_unit(
    order_line,
    shipping_zone,
    site_settings,
    address_usa,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager()
    order_line.unit_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )
    order_line.save()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    site_settings.company_address = address_usa
    site_settings.save()

    line_price = manager.calculate_order_line_unit(
        order, order_line, order_line.variant, order_line.variant.product
    )
    line_price = quantize_price(line_price, line_price.currency)

    assert line_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize("charge_taxes", [True, False])
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price(
    charge_taxes,
    checkout_with_item,
    shipping_zone,
    site_settings,
    address_usa,
    address,
    plugin_configuration,
):
    plugin_configuration()
    checkout = checkout_with_item
    total_price = TaxedMoney(
        net=Money("10.00", "USD") * 3, gross=Money("10.00", "USD") * 3
    )

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_line = lines[0]
    product = checkout_line.variant.product
    product.charge_taxes = charge_taxes
    product.save(update_fields=["charge_taxes"])

    manager = get_plugins_manager()

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = True
    site_settings.save()

    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    line_price = manager.calculate_checkout_line_unit_price(
        total_price,
        checkout_line.line.quantity,
        checkout_info,
        lines,
        checkout_line,
        checkout.shipping_address,
        [],
    )
    line_price = quantize_price(line_price, line_price.currency)

    if charge_taxes:
        assert line_price == TaxedMoney(
            net=Money("8.13", "USD"), gross=Money("10.00", "USD")
        )
    else:
        assert line_price == TaxedMoney(
            net=Money("10.00", "USD"), gross=Money("10.00", "USD")
        )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation(
    checkout_with_item,
    monkeypatch,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    discount_info,
    plugin_configuration,
):

    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager()
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)
    manager.preprocess_order_creation(checkout_info, discounts, lines)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_no_lines_data(
    checkout_with_item,
    monkeypatch,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    discount_info,
    plugin_configuration,
):

    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager()
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)
    manager.preprocess_order_creation(checkout_info, discounts)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_wrong_data(
    checkout_with_item,
    monkeypatch,
    address,
    shipping_zone,
    discount_info,
    plugin_configuration,
):
    plugin_configuration("wrong", "wrong")

    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_info, discounts, lines)


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch(monkeypatch):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x, y: {})
    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    tax_codes = get_cached_tax_codes_or_fetch(config)
    assert len(tax_codes) > 0


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch_wrong_response(monkeypatch):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x, y: {})
    config = AvataxConfiguration(
        username_or_account="wrong_data",
        password_or_license="wrong_data",
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    tax_codes = get_cached_tax_codes_or_fetch(config)
    assert len(tax_codes) == 0


def test_checkout_needs_new_fetch(
    monkeypatch, checkout_with_item, address, shipping_method
):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x: None)
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_method
    config = AvataxConfiguration(
        username_or_account="wrong_data",
        password_or_license="wrong_data",
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_data = generate_request_data_from_checkout(checkout_info, lines, config)
    assert taxes_need_new_fetch(checkout_data, str(checkout_with_item.token))


def test_taxes_need_new_fetch_uses_cached_data(
    monkeypatch, checkout_with_item, address
):

    checkout_with_item.shipping_address = address
    config = AvataxConfiguration(
        username_or_account="wrong_data",
        password_or_license="wrong_data",
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_data = generate_request_data_from_checkout(checkout_info, lines, config)
    monkeypatch.setattr(
        "saleor.plugins.avatax.cache.get", lambda x: [checkout_data, None]
    )
    assert not taxes_need_new_fetch(checkout_data, str(checkout_with_item.token))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate(
    monkeypatch,
    checkout_with_item,
    address,
    plugin_configuration,
    shipping_zone,
    site_settings,
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    checkout_info = CheckoutInfo(
        checkout=checkout_with_item,
        shipping_method=checkout_with_item.shipping_method,
        shipping_address=address,
        billing_address=None,
        channel=checkout_with_item.channel,
        user=None,
        shipping_method_channel_listings=None,
        valid_shipping_methods=[],
    )
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_line_info = lines[0]

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.23")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_for_product_with_charge_taxes_set_to_false(
    monkeypatch,
    checkout_with_item,
    address,
    plugin_configuration,
    shipping_zone,
    site_settings,
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(12, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    checkout_info = CheckoutInfo(
        checkout=checkout_with_item,
        shipping_method=checkout_with_item.shipping_method,
        shipping_address=address,
        billing_address=None,
        channel=checkout_with_item.channel,
        user=None,
        shipping_method_channel_listings=None,
        valid_shipping_methods=[],
    )
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_line_info = lines[0]
    product = checkout_line_info.product
    product.charge_taxes = False
    product.save(update_fields=["charge_taxes"])

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.0")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_for_product_type_with_non_taxable_product(
    monkeypatch,
    checkout_with_item,
    address,
    plugin_configuration,
    shipping_zone,
    site_settings,
    product_with_two_variants,
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"NT": "Non-Taxable Product"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(12, "USD"))

    manager = get_plugins_manager()

    product_type = ProductType.objects.create(name="non-taxable")
    product2 = product_with_two_variants
    product2.product_type = product_type
    manager.assign_tax_code_to_object_meta(product_type, "NT")
    product2.save()
    product_type.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    variant2 = product2.variants.first()
    checkout_info = CheckoutInfo(
        checkout=checkout_with_item,
        shipping_method=checkout_with_item.shipping_method,
        shipping_address=address,
        billing_address=None,
        channel=checkout_with_item.channel,
        user=None,
        shipping_method_channel_listings=None,
        valid_shipping_methods=[],
    )
    add_variant_to_checkout(checkout_info, variant2, 1)

    assert checkout_with_item.lines.count() == 2

    lines = fetch_checkout_lines(checkout_with_item)
    order = [checkout_with_item.lines.first().variant.pk, variant2.pk]
    lines.sort(key=lambda line: order.index(line.variant.pk))

    # when
    tax_rates = [
        manager.get_checkout_line_tax_rate(
            checkout_info,
            lines,
            checkout_line_info,
            checkout_with_item.shipping_address,
            [],
            unit_price,
        )
        for checkout_line_info in lines
    ]

    # then
    assert tax_rates[0] == Decimal("0.23")
    assert tax_rates[1] == Decimal("0.0")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_checkout_no_shipping_method_default_value_returned(
    monkeypatch, checkout_with_item, address, plugin_configuration, site_settings
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save(update_fields=["shipping_address"])

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_error_in_response(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: {"error": "Example error"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_line_tax_rate(
    monkeypatch, order_line, shipping_zone, plugin_configuration, site_settings, address
):
    # given
    order = order_line.order
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )

    unit_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))

    manager = get_plugins_manager()

    product = Product.objects.get(name=order_line.product_name)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_line_tax_rate(
        order,
        product,
        order_line.variant,
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_line_tax_rate_order_not_valid_default_value_returned(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    product = Product.objects.get(name=order_line.product_name)

    # when
    tax_rate = manager.get_order_line_tax_rate(
        order,
        product,
        order_line.variant,
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_line_tax_rate_error_in_response(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data",
        lambda *_: {"error": "Example error"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    product = Product.objects.get(name=order_line.product_name)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_line_tax_rate(
        order,
        product,
        order_line.variant,
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate(
    checkout_with_item, address, plugin_configuration, shipping_zone, site_settings
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = CheckoutInfo(
        checkout=checkout_with_item,
        shipping_method=checkout_with_item.shipping_method,
        shipping_address=address,
        billing_address=None,
        channel=checkout_with_item.channel,
        user=None,
        shipping_method_channel_listings=None,
        valid_shipping_methods=[],
    )

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate_checkout_not_valid_default_value_returned(
    monkeypatch, checkout_with_item, address, plugin_configuration
):
    # given
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.save(update_fields=["shipping_address"])

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate_error_in_response(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: {"error": "Example error"},
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate_skip_plugin(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin",
        lambda *_: True,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate(
    order_line, shipping_zone, plugin_configuration, site_settings, address
):
    # given
    site_settings.company_address = address
    site_settings.save()
    order = order_line.order
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate_order_not_valid_default_value_returned(
    order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate_error_in_response(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data",
        lambda *_: {"error": "Example error"},
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate_skip_plugin(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin",
        lambda *_: True,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


def test_get_plugin_configuration(settings, channel_USD):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager()
    plugin = manager.get_plugin(AvataxPlugin.PLUGIN_ID)

    configuration_fields = [
        configuration_item["name"] for configuration_item in plugin.configuration
    ]
    assert "Username or account" in configuration_fields
    assert "Password or license" in configuration_fields
    assert "Use sandbox" in configuration_fields
    assert "Company name" in configuration_fields
    assert "Autocommit" in configuration_fields


@patch("saleor.plugins.avatax.plugin.api_get_request")
def test_save_plugin_configuration(
    api_get_request_mock, settings, channel_USD, plugin_configuration
):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration()
    api_get_request_mock.return_value = {"authenticated": True}
    manager = get_plugins_manager()
    manager.save_plugin_configuration(
        AvataxPlugin.PLUGIN_ID,
        channel_USD.slug,
        {
            "active": True,
            "configuration": [
                {"name": "Username or account", "value": "test"},
                {"name": "Password or license", "value": "test"},
            ],
        },
    )
    manager.save_plugin_configuration(
        AvataxPlugin.PLUGIN_ID, channel_USD.slug, {"active": True}
    )
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxPlugin.PLUGIN_ID
    )
    assert plugin_configuration.active


@patch("saleor.plugins.avatax.plugin.api_get_request")
def test_save_plugin_configuration_authentication_failed(
    api_get_request_mock, settings, channel_USD, plugin_configuration
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(active=False)
    api_get_request_mock.return_value = {"authenticated": False}
    manager = get_plugins_manager()

    # when
    with pytest.raises(ValidationError) as e:
        manager.save_plugin_configuration(
            AvataxPlugin.PLUGIN_ID,
            channel_USD.slug,
            {
                "active": True,
                "configuration": [
                    {"name": "Username or account", "value": "test"},
                    {"name": "Password or license", "value": "test"},
                ],
            },
        )

    # then
    assert e._excinfo[1].args[0] == "Authentication failed. Please check provided data."
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxPlugin.PLUGIN_ID
    )
    assert not plugin_configuration.active


def test_save_plugin_configuration_cannot_be_enabled_without_config(
    settings, plugin_configuration, channel_USD
):
    plugin_configuration(None, None)
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager()
    with pytest.raises(ValidationError):
        manager.save_plugin_configuration(
            AvataxPlugin.PLUGIN_ID, channel_USD.slug, {"active": True}
        )


def test_show_taxes_on_storefront(plugin_configuration):
    plugin_configuration()
    manager = get_plugins_manager()
    assert manager.show_taxes_on_storefront() is False


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_order_created(api_post_request_task_mock, order, plugin_configuration):
    # given
    plugin_conf = plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-601",
        from_country="PL",
    )
    conf = {data["name"]: data["value"] for data in plugin_conf.configuration}

    manager = get_plugins_manager()

    # when
    manager.order_created(order)

    # then
    address = order.billing_address
    expected_request_data = {
        "createTransactionModel": {
            "companyCode": conf["Company name"],
            "type": TransactionType.INVOICE,
            "lines": [],
            "code": order.token,
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "customerCode": 0,
            "addresses": {
                "shipFrom": {
                    "line1": "Tęczowa 7",
                    "line2": None,
                    "city": "WROCŁAW",
                    "region": "",
                    "country": "PL",
                    "postalCode": "53-601",
                },
                "shipTo": {
                    "line1": address.street_address_1,
                    "line2": address.street_address_2,
                    "city": address.city,
                    "region": address.city_area or "",
                    "country": address.country.code,
                    "postalCode": address.postal_code,
                },
            },
            "commit": False,
            "currencyCode": order.currency,
            "email": order.user_email,
        }
    }

    conf_data = {
        "username_or_account": conf["Username or account"],
        "password_or_license": conf["Password or license"],
        "use_sandbox": conf["Use sandbox"],
        "company_name": conf["Company name"],
        "autocommit": conf["Autocommit"],
        "from_street_address": conf["from_street_address"],
        "from_city": conf["from_city"],
        "from_postal_code": conf["from_postal_code"],
        "from_country": conf["from_country"],
        "from_country_area": conf["from_country_area"],
    }

    api_post_request_task_mock.assert_called_once_with(
        "https://rest.avatax.com/api/v2/transactions/createoradjust",
        expected_request_data,
        conf_data,
        order.pk,
    )


@pytest.mark.vcr
def test_plugin_uses_configuration_from_db(
    plugin_configuration,
    monkeypatch,
    ship_to_pl_address,
    site_settings,
    address,
    checkout_with_item,
    shipping_zone,
    discount_info,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    configuration = plugin_configuration(
        username="2000134479", password="697932CFCBDE505B", sandbox=False
    )
    manager = get_plugins_manager()

    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)
    manager.preprocess_order_creation(checkout_info, discounts, lines)

    field_to_update = [
        {"name": "Username or account", "value": "New value"},
        {"name": "Password or license", "value": "Wrong pass"},
    ]
    AvataxPlugin._update_config_items(field_to_update, configuration.configuration)
    configuration.save()

    manager = get_plugins_manager()
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_info, discounts, lines)


def test_skip_disabled_plugin(settings, plugin_configuration):
    plugin_configuration(username=None, password=None)
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager()
    plugin: AvataxPlugin = manager.get_plugin(AvataxPlugin.PLUGIN_ID)

    assert (
        plugin._skip_plugin(
            previous_value=TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
        )
        is True
    )


def test_get_tax_code_from_object_meta(product, settings, plugin_configuration):
    product.store_value_in_metadata(
        {META_CODE_KEY: "KEY", META_DESCRIPTION_KEY: "DESC"}
    )
    plugin_configuration(username=None, password=None)
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager()
    tax_type = manager.get_tax_code_from_object_meta(product)

    assert isinstance(tax_type, TaxType)
    assert tax_type.code == "KEY"
    assert tax_type.description == "DESC"


def test_api_get_request_handles_request_errors(product, monkeypatch):
    mocked_response = Mock(side_effect=RequestException())
    monkeypatch.setattr("saleor.plugins.avatax.requests.get", mocked_response)

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    url = "https://www.avatax.api.com/some-get-path"

    response = api_get_request(
        url, config.username_or_account, config.password_or_license
    )

    assert response == {}
    assert mocked_response.called


def test_api_get_request_handles_json_errors(product, monkeypatch):
    mocked_response = Mock(side_effect=JSONDecodeError("", "", 0))
    monkeypatch.setattr("saleor.plugins.avatax.requests.get", mocked_response)

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    url = "https://www.avatax.api.com/some-get-path"

    response = api_get_request(
        url, config.username_or_account, config.password_or_license
    )

    assert response == {}
    assert mocked_response.called


def test_api_post_request_handles_request_errors(product, monkeypatch):
    mocked_response = Mock(side_effect=RequestException())
    monkeypatch.setattr("saleor.plugins.avatax.requests.post", mocked_response)

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    url = "https://www.avatax.api.com/some-get-path"

    response = api_post_request(url, {}, config)

    assert mocked_response.called
    assert response == {}


def test_api_post_request_handles_json_errors(product, monkeypatch):
    mocked_response = Mock(side_effect=JSONDecodeError("", "", 0))
    monkeypatch.setattr("saleor.plugins.avatax.requests.post", mocked_response)

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    url = "https://www.avatax.api.com/some-get-path"

    response = api_post_request(url, {}, config)

    assert mocked_response.called
    assert response == {}


def test_get_order_request_data_checks_when_taxes_are_included_to_price(
    order_with_lines, shipping_zone, site_settings, address
):
    site_settings.include_taxes_in_prices = True
    site_settings.company_address = address
    site_settings.save()
    method = shipping_zone.shipping_methods.get()
    line = order_with_lines.lines.first()
    line.unit_price_gross_amount = line.unit_price_net_amount
    line.save()

    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = method.name
    order_with_lines.shipping_method = method
    order_with_lines.save()

    config = AvataxConfiguration(
        username_or_account="",
        password_or_license="",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    request_data = get_order_request_data(order_with_lines, config)
    lines_data = request_data["createTransactionModel"]["lines"]

    assert all([line for line in lines_data if line["taxIncluded"] is True])


def test_get_order_request_data_checks_when_taxes_are_not_included_to_price(
    order_with_lines, shipping_zone, site_settings, address_usa
):
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = False
    site_settings.save()

    method = shipping_zone.shipping_methods.get()
    line = order_with_lines.lines.first()
    line.unit_price_gross_amount = line.unit_price_net_amount
    line.save()

    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = method.name
    order_with_lines.shipping_method = method
    order_with_lines.save()

    config = AvataxConfiguration(
        username_or_account="",
        password_or_license="",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )

    request_data = get_order_request_data(order_with_lines, config)
    lines_data = request_data["createTransactionModel"]["lines"]
    line_without_taxes = [line for line in lines_data if line["taxIncluded"] is False]
    # if order line has different .net and .gross we already added tax to it
    lines_with_taxes = [line for line in lines_data if line["taxIncluded"] is True]

    assert len(line_without_taxes) == 2
    assert len(lines_with_taxes) == 1

    assert line_without_taxes[0]["itemCode"] == line.product_sku


@patch("saleor.plugins.avatax.get_order_request_data")
@patch("saleor.plugins.avatax.get_cached_response_or_fetch")
def test_get_order_tax_data(
    get_cached_response_or_fetch_mock,
    get_order_request_data_mock,
    order,
    plugin_configuration,
):
    # given
    conf = plugin_configuration()

    return_value = {"id": 0, "code": "3d4893da", "companyId": 123}
    get_cached_response_or_fetch_mock.return_value = return_value

    # when
    response = get_order_tax_data(order, conf)

    # then
    get_order_request_data_mock.assert_called_once_with(order, conf)
    assert response == return_value


@patch("saleor.plugins.avatax.get_order_request_data")
@patch("saleor.plugins.avatax.get_cached_response_or_fetch")
def test_get_order_tax_data_raised_error(
    get_cached_response_or_fetch_mock,
    get_order_request_data_mock,
    order,
    plugin_configuration,
):
    # given
    conf = plugin_configuration()

    return_value = {"error": {"message": "test error"}}
    get_cached_response_or_fetch_mock.return_value = return_value

    # when
    with pytest.raises(TaxError) as e:
        get_order_tax_data(order, conf)

    # then
    assert e._excinfo[1].args[0] == return_value["error"]


@pytest.mark.parametrize(
    "shipping_address_none, shipping_method_none, billing_address_none, "
    "is_shipping_required, expected_is_valid",
    [
        (False, False, False, True, True),
        (True, True, False, True, False),
        (True, True, False, False, True),
        (False, True, False, True, False),
        (True, False, False, True, False),
    ],
)
def test_validate_adddress_details(
    shipping_address_none,
    shipping_method_none,
    billing_address_none,
    is_shipping_required,
    expected_is_valid,
    checkout_ready_to_complete,
):
    shipping_address = checkout_ready_to_complete.shipping_address
    shipping_address = None if shipping_address_none else shipping_address
    billing_address = checkout_ready_to_complete.billing_address
    billing_address = None if billing_address_none else billing_address
    address = shipping_address or billing_address
    shipping_method = checkout_ready_to_complete.shipping_method
    shipping_method = None if shipping_method_none else shipping_method
    is_valid = _validate_adddress_details(
        shipping_address, is_shipping_required, address, shipping_method
    )
    assert is_valid is expected_is_valid
