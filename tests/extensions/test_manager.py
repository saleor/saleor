from decimal import Decimal

import pytest
from django_countries.fields import Country
from prices import Money, TaxedMoney

from saleor.core.taxes import TaxType
from saleor.extensions.manager import ExtensionsManager, get_extensions_manager
from saleor.extensions.models import PluginConfiguration
from tests.extensions.sample_plugins import (
    ActivePaymentGateway,
    InactivePaymentGateway,
    PluginInactive,
    PluginSample,
)


def test_get_extensions_manager():
    manager_path = "saleor.extensions.manager.ExtensionsManager"
    plugin_path = "tests.extensions.sample_plugins.PluginSample"
    manager = get_extensions_manager(manager_path=manager_path, plugins=[plugin_path])
    assert isinstance(manager, ExtensionsManager)
    assert len(manager.plugins) == 1


@pytest.mark.parametrize(
    "plugins, total_amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_total(
    checkout_with_item, discount_info, plugins, total_amount
):
    currency = checkout_with_item.get_total().currency
    expected_total = Money(total_amount, currency)
    manager = ExtensionsManager(plugins=plugins)
    taxed_total = manager.calculate_checkout_total(checkout_with_item, [discount_info])
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins, subtotal_amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_subtotal(
    checkout_with_item, discount_info, plugins, subtotal_amount
):
    currency = checkout_with_item.get_total().currency
    expected_subtotal = Money(subtotal_amount, currency)
    taxed_subtotal = ExtensionsManager(plugins=plugins).calculate_checkout_subtotal(
        checkout_with_item, [discount_info]
    )
    assert TaxedMoney(expected_subtotal, expected_subtotal) == taxed_subtotal


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "0.0")],
)
def test_manager_calculates_checkout_shipping(
    checkout_with_item, discount_info, plugins, shipping_amount
):
    currency = checkout_with_item.get_total().currency
    expected_shipping_price = Money(shipping_amount, currency)
    taxed_shipping_price = ExtensionsManager(
        plugins=plugins
    ).calculate_checkout_shipping(checkout_with_item, [discount_info])
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_calculates_order_shipping(order_with_lines, plugins, shipping_amount):
    currency = order_with_lines.total.currency
    expected_shipping_price = Money(shipping_amount, currency)

    taxed_shipping_price = ExtensionsManager(plugins=plugins).calculate_order_shipping(
        order_with_lines
    )
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_line_total(
    checkout_with_item, discount_info, plugins, amount
):
    line = checkout_with_item.lines.all()[0]
    currency = line.get_total().currency
    expected_total = Money(amount, currency)
    taxed_total = ExtensionsManager(plugins=plugins).calculate_checkout_line_total(
        line, [discount_info]
    )
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "12.30")],
)
def test_manager_calculates_order_line(order_line, plugins, amount):
    currency = order_line.unit_price.currency
    expected_price = Money(amount, currency)
    unit_price = ExtensionsManager(plugins=plugins).calculate_order_line_unit(
        order_line
    )
    assert expected_price == unit_price.gross


@pytest.mark.parametrize(
    "plugins, tax_rate_list",
    [
        (
            ["tests.extensions.sample_plugins.PluginSample"],
            [TaxType(code="123", description="abc")],
        ),
        ([], []),
    ],
)
def test_manager_uses_get_tax_rate_choices(plugins, tax_rate_list):
    assert (
        tax_rate_list == ExtensionsManager(plugins=plugins).get_tax_rate_type_choices()
    )


@pytest.mark.parametrize(
    "plugins, show_taxes",
    [(["tests.extensions.sample_plugins.PluginSample"], True), ([], False)],
)
def test_manager_show_taxes_on_storefront(plugins, show_taxes):
    assert show_taxes == ExtensionsManager(plugins=plugins).show_taxes_on_storefront()


@pytest.mark.parametrize(
    "plugins, taxes_enabled",
    [(["tests.extensions.sample_plugins.PluginSample"], True), ([], False)],
)
def test_manager_taxes_are_enabled(plugins, taxes_enabled):
    assert taxes_enabled == ExtensionsManager(plugins=plugins).taxes_are_enabled()


@pytest.mark.parametrize(
    "plugins, price",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_product(product, plugins, price):
    country = Country("PL")
    variant = product.variants.all()[0]
    currency = variant.get_price().currency
    expected_price = Money(price, currency)
    taxed_price = ExtensionsManager(plugins=plugins).apply_taxes_to_product(
        product, variant.get_price(), country
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price


@pytest.mark.parametrize(
    "plugins, price_amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_shipping(
    shipping_method, address, plugins, price_amount
):
    expected_price = Money(price_amount, "USD")
    taxed_price = ExtensionsManager(plugins=plugins).apply_taxes_to_shipping(
        shipping_method.price, address
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.extensions.sample_plugins.PluginSample"], "15.0"), ([], "0")],
)
def test_manager_get_tax_rate_percentage_value(plugins, amount, product):
    country = Country("PL")
    tax_rate_value = ExtensionsManager(plugins=plugins).get_tax_rate_percentage_value(
        product, country
    )
    assert tax_rate_value == Decimal(amount)


def test_manager_get_plugin_configurations():
    plugins = [
        "tests.extensions.sample_plugins.PluginSample",
        "tests.extensions.sample_plugins.PluginInactive",
    ]
    manager = ExtensionsManager(plugins=plugins)
    configurations = manager.get_plugin_configurations()
    assert len(configurations) == len(plugins)
    assert set(configurations) == set(list(PluginConfiguration.objects.all()))


def test_manager_get_plugin_configuration(plugin_configuration):
    plugins = [
        "tests.extensions.sample_plugins.PluginSample",
        "tests.extensions.sample_plugins.PluginInactive",
    ]
    manager = ExtensionsManager(plugins=plugins)
    configuration = manager.get_plugin_configuration(plugin_name="PluginSample")
    configuration_from_db = PluginConfiguration.objects.get(name="PluginSample")
    assert configuration == configuration_from_db


def test_manager_save_plugin_configuration(plugin_configuration):
    plugins = ["tests.extensions.sample_plugins.PluginSample"]
    manager = ExtensionsManager(plugins=plugins)
    configuration = manager.get_plugin_configuration(plugin_name="PluginSample")
    manager.save_plugin_configuration("PluginSample", {"active": False})
    configuration.refresh_from_db()
    assert not configuration.active


def test_plugin_updates_configuration_shape(
    new_config,
    new_config_structure,
    manager_with_plugin_enabled,
    plugin_configuration,
    monkeypatch,
):
    def new_default_configuration():
        defaults = {
            "name": "PluginSample",
            "description": "",
            "active": True,
            "configuration": plugin_configuration.configuration + [new_config],
        }
        return defaults

    config_structure = PluginSample.CONFIG_STRUCTURE.copy()
    config_structure["Foo"] = new_config_structure
    monkeypatch.setattr(PluginSample, "CONFIG_STRUCTURE", config_structure)

    monkeypatch.setattr(
        PluginSample, "_get_default_configuration", new_default_configuration
    )

    configuration = manager_with_plugin_enabled.get_plugin_configuration(
        plugin_name="PluginSample"
    )

    assert len(configuration.configuration) == 5
    assert configuration.configuration[-1] == {**new_config, **new_config_structure}


def test_plugin_add_new_configuration(
    new_config,
    new_config_structure,
    manager_with_plugin_without_configuration_enabled,
    inactive_plugin_configuration,
    monkeypatch,
):
    def new_default_configuration():
        defaults = {
            "name": "PluginInactive",
            "description": "",
            "active": True,
            "configuration": [new_config],
        }
        return defaults

    monkeypatch.setattr(
        PluginInactive, "_get_default_configuration", new_default_configuration
    )
    config_structure = {"Foo": new_config_structure}
    monkeypatch.setattr(PluginInactive, "CONFIG_STRUCTURE", config_structure)
    config = manager_with_plugin_without_configuration_enabled.get_plugin_configuration(
        plugin_name="PluginInactive"
    )
    assert len(config.configuration) == 1
    assert config.configuration[0] == {**new_config, **new_config_structure}


def test_manager_serve_list_of_payment_gateways():
    expected_gateway = {
        "name": ActivePaymentGateway.PLUGIN_NAME,
        "config": ActivePaymentGateway.CLIENT_CONFIG,
    }
    plugins = [
        "tests.extensions.sample_plugins.PluginSample",
        "tests.extensions.sample_plugins.ActivePaymentGateway",
        "tests.extensions.sample_plugins.InactivePaymentGateway",
    ]
    manager = ExtensionsManager(plugins=plugins)
    assert manager.list_payment_gateways() == [expected_gateway]


def test_manager_serve_list_all_payment_gateways():
    expected_gateways = [
        {
            "name": ActivePaymentGateway.PLUGIN_NAME,
            "config": ActivePaymentGateway.CLIENT_CONFIG,
        },
        {"name": InactivePaymentGateway.PLUGIN_NAME, "config": []},
    ]

    plugins = [
        "tests.extensions.sample_plugins.ActivePaymentGateway",
        "tests.extensions.sample_plugins.InactivePaymentGateway",
    ]
    manager = ExtensionsManager(plugins=plugins)
    assert manager.list_payment_gateways(active_only=False) == expected_gateways
