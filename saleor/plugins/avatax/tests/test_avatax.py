import datetime
from decimal import Decimal
from json import JSONDecodeError
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from prices import Money, TaxedMoney
from requests import RequestException

from ....checkout import CheckoutLineInfo
from ....checkout.utils import add_variant_to_checkout, fetch_checkout_lines
from ....core.prices import quantize_price
from ....core.taxes import TaxError, TaxType
from ....product.models import Product
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


@pytest.fixture
def plugin_configuration(db):
    def set_configuration(username="test", password="test", sandbox=True):
        data = {
            "active": True,
            "name": AvataxPlugin.PLUGIN_NAME,
            "configuration": [
                {"name": "Username or account", "value": username},
                {"name": "Password or license", "value": password},
                {"name": "Use sandbox", "value": sandbox},
                {"name": "Company name", "value": "DEFAULT"},
                {"name": "Autocommit", "value": False},
            ],
        }
        configuration = PluginConfiguration.objects.create(
            identifier=AvataxPlugin.PLUGIN_ID, **data
        )
        return configuration

    return set_configuration


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
def test_calculate_checkout_line_total(
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    discount_info,
    checkout_with_item,
    address,
    address_usa,
    site_settings,
    monkeypatch,
    shipping_zone,
    plugin_configuration,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}
    manager.assign_tax_code_to_object_meta(product.product_type, "PC040156")
    product.save()
    product.product_type.save()
    discounts = [discount_info] if with_discount else None
    channel = checkout_with_item.channel
    channel_listing = line.variant.channel_listings.get(channel=channel)
    total = manager.calculate_checkout_line_total(
        checkout_with_item,
        line,
        line.variant,
        line.variant.product,
        [],
        checkout_with_item.shipping_address,
        channel,
        channel_listing,
        discounts,
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


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
    address_usa,
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
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    site_settings.company_address = address_usa
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
    add_variant_to_checkout(
        checkout_with_item, product_with_single_variant.variants.get()
    )

    discounts = [discount_info] if with_discount else None
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(
        checkout_with_item, lines, address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


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
    address_usa,
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
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    site_settings.company_address = address_usa
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
    add_variant_to_checkout(
        checkout_with_item, product_with_single_variant.variants.get()
    )

    discounts = [discount_info] if with_discount else None
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(
        checkout_with_item, lines, address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
def test_calculate_checkout_shipping(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    address_usa,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    site_settings.company_address = address_usa
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines = fetch_checkout_lines(checkout_with_item)
    shipping_price = manager.calculate_checkout_shipping(
        checkout_with_item, lines, address, [discount_info]
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
    address_usa,
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
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    discounts = [discount_info] if with_discount else None
    add_variant_to_checkout(checkout_with_item, variant, 2)
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_subtotal(
        checkout_with_item, lines, address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
def test_calculate_order_shipping(
    order_line, shipping_zone, site_settings, address_usa, plugin_configuration
):
    plugin_configuration()
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    site_settings.company_address = address_usa
    site_settings.save()

    price = manager.calculate_order_shipping(order)
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


@pytest.mark.vcr
def test_calculate_order_line_unit(
    order_line,
    shipping_zone,
    site_settings,
    address_usa,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
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

    line_price = manager.calculate_order_line_unit(order_line)
    line_price = quantize_price(line_price, line_price.currency)

    assert line_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.vcr
def test_preprocess_order_creation(
    checkout_with_item,
    monkeypatch,
    address,
    address_usa,
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
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    site_settings.company_address = address_usa
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    manager.preprocess_order_creation(checkout_with_item, discounts)


@pytest.mark.vcr
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
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_with_item, discounts)


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch(monkeypatch, settings):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x, y: {})
    config = AvataxConfiguration(username_or_account="test", password_or_license="test")
    tax_codes = get_cached_tax_codes_or_fetch(config)
    assert len(tax_codes) > 0


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch_wrong_response(monkeypatch):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x, y: {})
    config = AvataxConfiguration(
        username_or_account="wrong_data", password_or_license="wrong_data"
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
        username_or_account="wrong_data", password_or_license="wrong_data"
    )
    checkout_data = generate_request_data_from_checkout(checkout_with_item, config)
    assert taxes_need_new_fetch(checkout_data, str(checkout_with_item.token))


def test_taxes_need_new_fetch_uses_cached_data(
    monkeypatch, checkout_with_item, address
):

    checkout_with_item.shipping_address = address
    config = AvataxConfiguration(
        username_or_account="wrong_data", password_or_license="wrong_data"
    )
    checkout_data = generate_request_data_from_checkout(checkout_with_item, config)
    monkeypatch.setattr(
        "saleor.plugins.avatax.cache.get", lambda x: [checkout_data, None]
    )
    assert not taxes_need_new_fetch(checkout_data, str(checkout_with_item.token))


AVALARA_TAX_DATA = {
    "id": 0,
    "companyId": 123,
    "date": "2020-12-28",
    "paymentDate": "2020-12-28",
    "status": "Temporary",
    "type": "SalesOrder",
    "lines": [
        {
            "itemCode": "3456",
            "details": [{"taxType": "Sales", "rate": 0.055, "tax": 2.03}],
        },
        {"itemCode": "Shipping", "details": [{"rate": 0.08, "tax": 1.5}]},
    ],
    "summary": [
        {
            "country": "US",
            "region": "NE",
            "jurisType": "State",
            "jurisCode": "31",
            "jurisName": "NEBRASKA",
            "taxAuthorityType": 45,
            "stateAssignedNo": "",
            "taxType": "Sales",
            "taxSubType": "S",
            "taxName": "NE STATE TAX",
            "rateType": "General",
            "taxable": 36.94,
            "rate": 0.055,
            "tax": 2.03,
            "taxCalculated": 2.03,
            "nonTaxable": 0.0,
            "exemption": 0.0,
        }
    ],
}


def test_get_checkout_line_tax_rate(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: AVALARA_TAX_DATA,
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    line = checkout_with_item.lines.first()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.055")


def test_get_checkout_line_tax_rate_checkout_not_valid_default_value_returned(
    monkeypatch, checkout_with_item, address, plugin_configuration
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: AVALARA_TAX_DATA,
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    line = checkout_with_item.lines.first()

    checkout_with_item.shipping_address = address
    checkout_with_item.save(update_fields=["shipping_address"])

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


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

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    line = checkout_with_item.lines.first()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


def test_get_order_line_tax_rate(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data", lambda *_: AVALARA_TAX_DATA
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

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
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.055")


def test_get_order_line_tax_rate_order_not_valid_default_value_returned(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data", lambda *_: AVALARA_TAX_DATA
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    product = Product.objects.get(name=order_line.product_name)

    # when
    tax_rate = manager.get_order_line_tax_rate(
        order,
        product,
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


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

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

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
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


def test_get_checkout_shipping_tax_rate(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: AVALARA_TAX_DATA,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    line = checkout_with_item.lines.first()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_with_item,
        [checkout_line_info],
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.08")


def test_get_checkout_shipping_tax_rate_checkout_not_valid_default_value_returned(
    monkeypatch, checkout_with_item, address, plugin_configuration
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: AVALARA_TAX_DATA,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    line = checkout_with_item.lines.first()

    checkout_with_item.shipping_address = address
    checkout_with_item.save(update_fields=["shipping_address"])

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_with_item,
        [checkout_line_info],
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


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

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    line = checkout_with_item.lines.first()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_with_item,
        [checkout_line_info],
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


def test_get_checkout_shipping_tax_rate_skip_plugin(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: {"error": "Example error"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin",
        lambda *_: True,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])
    line = checkout_with_item.lines.first()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_with_item,
        [checkout_line_info],
        checkout_with_item.shipping_address,
        [],
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


def test_get_order_shipping_tax_rate(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data", lambda *_: AVALARA_TAX_DATA
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.08")


def test_get_order_shipping_tax_rate_order_not_valid_default_value_returned(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data", lambda *_: AVALARA_TAX_DATA
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


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

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


def test_get_order_shipping_tax_rate_skip_plugin(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data",
        lambda *_: {"error": "Example error"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin",
        lambda *_: True,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


def test_get_plugin_configuration(settings):
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
def test_save_plugin_configuration(api_get_request_mock, settings):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    api_get_request_mock.return_value = {"authenticated": True}
    manager = get_plugins_manager()
    manager.save_plugin_configuration(
        AvataxPlugin.PLUGIN_ID,
        {
            "active": True,
            "configuration": [
                {"name": "Username or account", "value": "test"},
                {"name": "Password or license", "value": "test"},
            ],
        },
    )
    manager.save_plugin_configuration(AvataxPlugin.PLUGIN_ID, {"active": True})
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxPlugin.PLUGIN_ID
    )
    assert plugin_configuration.active


@patch("saleor.plugins.avatax.plugin.api_get_request")
def test_save_plugin_configuration_authentication_failed(
    api_get_request_mock, settings
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    api_get_request_mock.return_value = {"authenticated": False}
    manager = get_plugins_manager()

    # when
    with pytest.raises(ValidationError) as e:
        manager.save_plugin_configuration(
            AvataxPlugin.PLUGIN_ID,
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
    settings, plugin_configuration
):
    plugin_configuration(None, None)
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager()
    with pytest.raises(ValidationError):
        manager.save_plugin_configuration(AvataxPlugin.PLUGIN_ID, {"active": True})


def test_show_taxes_on_storefront(plugin_configuration):
    plugin_configuration()
    manager = get_plugins_manager()
    assert manager.show_taxes_on_storefront() is False


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
def test_order_created(api_post_request_task_mock, order, plugin_configuration):
    # given
    plugin_conf = plugin_configuration()
    conf = {data["name"]: data["value"] for data in plugin_conf.configuration}

    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

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
                    "line1": None,
                    "line2": None,
                    "city": None,
                    "region": None,
                    "country": None,
                    "postalCode": None,
                },
                "shipTo": {
                    "line1": address.street_address_1,
                    "line2": address.street_address_2,
                    "city": address.city,
                    "region": address.city_area or "",
                    "country": address.country,
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
    }

    api_post_request_task_mock.assert_called_once_with(
        "https://sandbox-rest.avatax.com/api/v2/transactions/createoradjust",
        expected_request_data,
        conf_data,
        order.pk,
    )


@pytest.mark.vcr
def test_plugin_uses_configuration_from_db(
    plugin_configuration,
    monkeypatch,
    address_usa,
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
    site_settings.company_address = address_usa
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]

    manager.preprocess_order_creation(checkout_with_item, discounts)

    field_to_update = [
        {"name": "Username or account", "value": "New value"},
        {"name": "Password or license", "value": "Wrong pass"},
    ]
    AvataxPlugin._update_config_items(field_to_update, configuration.configuration)
    configuration.save()

    manager = get_plugins_manager()
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_with_item, discounts)


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
    )
    url = "https://www.avatax.api.com/some-get-path"

    response = api_post_request(url, {}, config)

    assert mocked_response.called
    assert response == {}


def test_get_order_request_data_checks_when_taxes_are_included_to_price(
    order_with_lines, shipping_zone, site_settings, address_usa
):
    site_settings.include_taxes_in_prices = True
    site_settings.company_address = address_usa
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
