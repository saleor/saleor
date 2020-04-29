from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError
from prices import Money, TaxedMoney

from saleor.checkout.utils import add_variant_to_checkout
from saleor.core.taxes import TaxError, quantize_price
from saleor.plugins.avatax import (
    AvataxConfiguration,
    checkout_needs_new_fetch,
    generate_request_data_from_checkout,
    get_cached_tax_codes_or_fetch,
)
from saleor.plugins.avatax.plugin import AvataxPlugin
from saleor.plugins.manager import get_plugins_manager
from saleor.plugins.models import PluginConfiguration


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
    manager.assign_tax_code_to_object_meta(product, "PC040156")
    product.save()
    discounts = [discount_info] if with_discount else None
    total = manager.calculate_checkout_line_total(line, discounts)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, taxes_in_prices",
    [
        (True, "20.33", "25.00", "0.0", True),
        (True, "20.00", "25.75", "5.0", False),
        (False, "40.00", "49.20", "0.0", False),
        (False, "29.52", "37.00", "3.0", True),
    ],
)
def test_calculate_checkout_total(
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
    checkout_with_item,
    discount_info,
    shipping_zone,
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
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices

    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "PC040156")
    product.save()

    discounts = [discount_info] if with_discount else None
    total = manager.calculate_checkout_total(
        checkout_with_item, list(checkout_with_item), discounts
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
    shipping_price = manager.calculate_checkout_shipping(
        checkout_with_item, list(checkout_with_item), [discount_info]
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
    total = manager.calculate_checkout_subtotal(
        checkout_with_item, list(checkout_with_item), discounts
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
    order_line, shipping_zone, site_settings, address_usa, plugin_configuration,
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


def test_checkout_needs_new_fetch(monkeypatch, checkout_with_item, address):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x: None)
    checkout_with_item.shipping_address = address
    config = AvataxConfiguration(
        username_or_account="wrong_data", password_or_license="wrong_data"
    )
    checkout_data = generate_request_data_from_checkout(checkout_with_item, config)
    assert checkout_needs_new_fetch(checkout_data, str(checkout_with_item.token))


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


def test_save_plugin_configuration(settings):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager()
    manager.save_plugin_configuration(
        AvataxPlugin.PLUGIN_ID,
        {
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


def test_order_created(order, monkeypatch, plugin_configuration):
    plugin_configuration()
    manager = get_plugins_manager(plugins=["saleor.plugins.avatax.plugin.AvataxPlugin"])

    mocked_task = Mock()
    monkeypatch.setattr("saleor.plugins.avatax.plugin.get_order_tax_data", Mock())
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.api_post_request_task.delay", mocked_task,
    )

    manager.order_created(order)
    # TODO test assert with
    assert mocked_task.called


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
