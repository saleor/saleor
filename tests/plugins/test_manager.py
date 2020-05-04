from decimal import Decimal

import pytest
from django_countries.fields import Country
from prices import Money, TaxedMoney

from saleor.core.taxes import TaxType
from saleor.plugins.manager import PluginsManager, get_plugins_manager
from saleor.plugins.models import PluginConfiguration
from tests.plugins.sample_plugins import (
    ActivePaymentGateway,
    InactivePaymentGateway,
    PluginInactive,
    PluginSample,
)


def test_get_plugins_manager():
    manager_path = "saleor.plugins.manager.PluginsManager"
    plugin_path = "tests.plugins.sample_plugins.PluginSample"
    manager = get_plugins_manager(manager_path=manager_path, plugins=[plugin_path])
    assert isinstance(manager, PluginsManager)
    assert len(manager.plugins) == 1


@pytest.mark.parametrize(
    "plugins, total_amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_total(
    checkout_with_item, discount_info, plugins, total_amount
):
    currency = checkout_with_item.currency
    expected_total = Money(total_amount, currency)
    manager = PluginsManager(plugins=plugins)
    taxed_total = manager.calculate_checkout_total(
        checkout_with_item, list(checkout_with_item), [discount_info]
    )
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins, subtotal_amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_subtotal(
    checkout_with_item, discount_info, plugins, subtotal_amount
):
    currency = checkout_with_item.currency
    expected_subtotal = Money(subtotal_amount, currency)
    taxed_subtotal = PluginsManager(plugins=plugins).calculate_checkout_subtotal(
        checkout_with_item, list(checkout_with_item), [discount_info]
    )
    assert TaxedMoney(expected_subtotal, expected_subtotal) == taxed_subtotal


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "0.0")],
)
def test_manager_calculates_checkout_shipping(
    checkout_with_item, discount_info, plugins, shipping_amount
):
    currency = checkout_with_item.currency
    expected_shipping_price = Money(shipping_amount, currency)
    taxed_shipping_price = PluginsManager(plugins=plugins).calculate_checkout_shipping(
        checkout_with_item, list(checkout_with_item), [discount_info]
    )
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_calculates_order_shipping(order_with_lines, plugins, shipping_amount):
    currency = order_with_lines.total.currency
    expected_shipping_price = Money(shipping_amount, currency)

    taxed_shipping_price = PluginsManager(plugins=plugins).calculate_order_shipping(
        order_with_lines
    )
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_line_total(
    checkout_with_item, discount_info, plugins, amount
):
    line = checkout_with_item.lines.all()[0]
    currency = checkout_with_item.currency
    expected_total = Money(amount, currency)
    taxed_total = PluginsManager(plugins=plugins).calculate_checkout_line_total(
        line, [discount_info]
    )
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "12.30")],
)
def test_manager_calculates_order_line(order_line, plugins, amount):
    currency = order_line.unit_price.currency
    expected_price = Money(amount, currency)
    unit_price = PluginsManager(plugins=plugins).calculate_order_line_unit(order_line)
    assert expected_price == unit_price.gross


@pytest.mark.parametrize(
    "plugins, tax_rate_list",
    [
        (
            ["tests.plugins.sample_plugins.PluginSample"],
            [TaxType(code="123", description="abc")],
        ),
        ([], []),
    ],
)
def test_manager_uses_get_tax_rate_choices(plugins, tax_rate_list):
    assert tax_rate_list == PluginsManager(plugins=plugins).get_tax_rate_type_choices()


@pytest.mark.parametrize(
    "plugins, show_taxes",
    [(["tests.plugins.sample_plugins.PluginSample"], True), ([], False)],
)
def test_manager_show_taxes_on_storefront(plugins, show_taxes):
    assert show_taxes == PluginsManager(plugins=plugins).show_taxes_on_storefront()


@pytest.mark.parametrize(
    "plugins, price",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_product(product, plugins, price):
    country = Country("PL")
    variant = product.variants.all()[0]
    currency = variant.get_price().currency
    expected_price = Money(price, currency)
    taxed_price = PluginsManager(plugins=plugins).apply_taxes_to_product(
        product, variant.get_price(), country
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price


@pytest.mark.parametrize(
    "plugins, price_amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_shipping(
    shipping_method, address, plugins, price_amount
):
    expected_price = Money(price_amount, "USD")
    taxed_price = PluginsManager(plugins=plugins).apply_taxes_to_shipping(
        shipping_method.price, address
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.plugins.sample_plugins.PluginSample"], "15.0"), ([], "0")],
)
def test_manager_get_tax_rate_percentage_value(plugins, amount, product):
    country = Country("PL")
    tax_rate_value = PluginsManager(plugins=plugins).get_tax_rate_percentage_value(
        product, country
    )
    assert tax_rate_value == Decimal(amount)


def test_manager_get_plugin_configurations(plugin_configuration):
    plugins = [
        "tests.plugins.sample_plugins.PluginSample",
        "tests.plugins.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    plugin_configs = manager._plugin_configs.values()
    assert len(plugin_configs) == 1
    assert set(plugin_configs) == set(list(PluginConfiguration.objects.all()))


def test_manager_get_plugin_configuration(plugin_configuration):
    plugins = [
        "tests.plugins.sample_plugins.PluginSample",
        "tests.plugins.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    plugin = manager.get_plugin(PluginSample.PLUGIN_ID)
    configuration_from_db = PluginConfiguration.objects.get(
        identifier=PluginSample.PLUGIN_ID
    )
    assert plugin.DEFAULT_CONFIGURATION == configuration_from_db.configuration


def test_manager_save_plugin_configuration(plugin_configuration):
    plugins = ["tests.plugins.sample_plugins.PluginSample"]
    manager = PluginsManager(plugins=plugins)
    manager.save_plugin_configuration(PluginSample.PLUGIN_ID, {"active": False})
    plugin_configuration.refresh_from_db()
    assert not plugin_configuration.active


def test_plugin_updates_configuration_shape(
    new_config, new_config_structure, plugin_configuration, monkeypatch,
):

    config_structure = PluginSample.CONFIG_STRUCTURE.copy()
    config_structure["Foo"] = new_config_structure
    monkeypatch.setattr(PluginSample, "CONFIG_STRUCTURE", config_structure)

    monkeypatch.setattr(
        PluginSample,
        "DEFAULT_CONFIGURATION",
        plugin_configuration.configuration + [new_config],
    )

    manager = PluginsManager(plugins=["tests.plugins.sample_plugins.PluginSample"])
    plugin = manager.get_plugin(PluginSample.PLUGIN_ID)

    assert len(plugin.configuration) == 5
    assert plugin.configuration[-1] == {**new_config, **new_config_structure}


def test_plugin_add_new_configuration(
    new_config, new_config_structure, monkeypatch,
):
    monkeypatch.setattr(PluginInactive, "DEFAULT_ACTIVE", True)
    monkeypatch.setattr(
        PluginInactive, "DEFAULT_CONFIGURATION", [new_config],
    )
    config_structure = {"Foo": new_config_structure}
    monkeypatch.setattr(PluginInactive, "CONFIG_STRUCTURE", config_structure)
    manager = PluginsManager(plugins=["tests.plugins.sample_plugins.PluginInactive"])
    plugin = manager.get_plugin(PluginInactive.PLUGIN_ID)
    assert len(plugin.configuration) == 1
    assert plugin.configuration[0] == {**new_config, **new_config_structure}


def test_manager_serve_list_of_payment_gateways():
    expected_gateway = {
        "id": ActivePaymentGateway.PLUGIN_ID,
        "name": ActivePaymentGateway.PLUGIN_NAME,
        "config": ActivePaymentGateway.CLIENT_CONFIG,
    }
    plugins = [
        "tests.plugins.sample_plugins.PluginSample",
        "tests.plugins.sample_plugins.ActivePaymentGateway",
        "tests.plugins.sample_plugins.InactivePaymentGateway",
    ]
    manager = PluginsManager(plugins=plugins)
    assert manager.list_payment_gateways() == [expected_gateway]


def test_manager_serve_list_all_payment_gateways():
    expected_gateways = [
        {
            "id": ActivePaymentGateway.PLUGIN_ID,
            "name": ActivePaymentGateway.PLUGIN_NAME,
            "config": ActivePaymentGateway.CLIENT_CONFIG,
        },
        {
            "id": InactivePaymentGateway.PLUGIN_ID,
            "name": InactivePaymentGateway.PLUGIN_NAME,
            "config": [],
        },
    ]

    plugins = [
        "tests.plugins.sample_plugins.ActivePaymentGateway",
        "tests.plugins.sample_plugins.InactivePaymentGateway",
    ]
    manager = PluginsManager(plugins=plugins)
    assert manager.list_payment_gateways(active_only=False) == expected_gateways
