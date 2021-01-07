import json
from decimal import Decimal

import pytest
from django.http import HttpResponseNotFound, JsonResponse
from django_countries.fields import Country
from prices import Money, TaxedMoney

from ...checkout import CheckoutLineInfo
from ...checkout.utils import fetch_checkout_lines
from ...core.taxes import TaxType
from ...payment.interface import PaymentGateway
from ...product.models import Product
from ..manager import PluginsManager, get_plugins_manager
from ..models import PluginConfiguration
from ..tests.sample_plugins import (
    ActiveDummyPaymentGateway,
    ActivePaymentGateway,
    InactivePaymentGateway,
    PluginInactive,
    PluginSample,
)


def test_get_plugins_manager():
    manager_path = "saleor.plugins.manager.PluginsManager"
    plugin_path = "saleor.plugins.tests.sample_plugins.PluginSample"
    manager = get_plugins_manager(manager_path=manager_path, plugins=[plugin_path])
    assert isinstance(manager, PluginsManager)
    assert len(manager.plugins) == 1


@pytest.mark.parametrize(
    "plugins, total_amount",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_total(
    checkout_with_item, discount_info, plugins, total_amount
):
    currency = checkout_with_item.currency
    expected_total = Money(total_amount, currency)
    manager = PluginsManager(plugins=plugins)
    lines = fetch_checkout_lines(checkout_with_item)
    taxed_total = manager.calculate_checkout_total(
        checkout_with_item, lines, None, [discount_info]
    )
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins, subtotal_amount",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_subtotal(
    checkout_with_item, discount_info, plugins, subtotal_amount
):
    currency = checkout_with_item.currency
    expected_subtotal = Money(subtotal_amount, currency)
    lines = fetch_checkout_lines(checkout_with_item)
    taxed_subtotal = PluginsManager(plugins=plugins).calculate_checkout_subtotal(
        checkout_with_item, lines, None, [discount_info]
    )
    assert TaxedMoney(expected_subtotal, expected_subtotal) == taxed_subtotal


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "0.0")],
)
def test_manager_calculates_checkout_shipping(
    checkout_with_item, discount_info, plugins, shipping_amount
):
    currency = checkout_with_item.currency
    expected_shipping_price = Money(shipping_amount, currency)
    lines = fetch_checkout_lines(checkout_with_item)
    taxed_shipping_price = PluginsManager(plugins=plugins).calculate_checkout_shipping(
        checkout_with_item, lines, None, [discount_info]
    )
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
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
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_line_total(
    checkout_with_item, discount_info, plugins, amount
):
    line = checkout_with_item.lines.all()[0]
    channel = checkout_with_item.channel
    channel_listing = line.variant.channel_listings.get(channel=channel)
    currency = checkout_with_item.currency
    expected_total = Money(amount, currency)
    taxed_total = PluginsManager(plugins=plugins).calculate_checkout_line_total(
        checkout_with_item,
        line,
        line.variant,
        line.variant.product,
        [],
        checkout_with_item.shipping_address,
        channel,
        channel_listing,
        [discount_info],
    )
    assert TaxedMoney(expected_total, expected_total) == taxed_total


def test_manager_get_checkout_line_tax_rate_sample_plugin(
    checkout_with_item, discount_info
):
    line = checkout_with_item.lines.all()[0]
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    tax_rate = PluginsManager(plugins=plugins).get_checkout_line_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [discount_info],
        unit_price,
    )
    assert tax_rate == Decimal("0.08")


@pytest.mark.parametrize(
    "unit_price, expected_tax_rate",
    [
        (TaxedMoney(Money(12, "USD"), Money(15, "USD")), Decimal("0.25")),
        (Decimal("0.0"), Decimal("0.0")),
    ],
)
def test_manager_get_checkout_line_tax_rate_no_plugins(
    checkout_with_item, discount_info, unit_price, expected_tax_rate
):
    line = checkout_with_item.lines.all()[0]
    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )
    tax_rate = PluginsManager(plugins=[]).get_checkout_line_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [discount_info],
        unit_price,
    )
    assert tax_rate == expected_tax_rate


def test_manager_get_order_line_tax_rate_sample_plugin(order_with_lines):
    order = order_with_lines
    line = order.lines.first()
    product = Product.objects.get(name=line.product_name)
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))
    tax_rate = PluginsManager(plugins=plugins).get_order_line_tax_rate(
        order,
        product,
        None,
        unit_price,
    )
    assert tax_rate == Decimal("0.08")


@pytest.mark.parametrize(
    "unit_price, expected_tax_rate",
    [
        (TaxedMoney(Money(12, "USD"), Money(15, "USD")), Decimal("0.25")),
        (Decimal("0.0"), Decimal("0.0")),
    ],
)
def test_manager_get_order_line_tax_rate_no_plugins(
    order_with_lines, unit_price, expected_tax_rate
):
    order = order_with_lines
    line = order.lines.first()
    product = Product.objects.get(name=line.product_name)
    tax_rate = PluginsManager(plugins=[]).get_order_line_tax_rate(
        order,
        product,
        None,
        unit_price,
    )
    assert tax_rate == expected_tax_rate


def test_manager_get_checkout_shipping_tax_rate_sample_plugin(
    checkout_with_item, discount_info
):
    line = checkout_with_item.lines.all()[0]
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    shipping_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    tax_rate = PluginsManager(plugins=plugins).get_checkout_shipping_tax_rate(
        checkout_with_item,
        [checkout_line_info],
        checkout_with_item.shipping_address,
        [discount_info],
        shipping_price,
    )
    assert tax_rate == Decimal("0.08")


@pytest.mark.parametrize(
    "shipping_price, expected_tax_rate",
    [
        (TaxedMoney(Money(12, "USD"), Money(14, "USD")), Decimal("0.1667")),
        (Decimal("0.0"), Decimal("0.0")),
    ],
)
def test_manager_get_checkout_shipping_tax_rate_no_plugins(
    checkout_with_item, discount_info, shipping_price, expected_tax_rate
):
    line = checkout_with_item.lines.all()[0]
    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )
    tax_rate = PluginsManager(plugins=[]).get_checkout_shipping_tax_rate(
        checkout_with_item,
        [checkout_line_info],
        checkout_with_item.shipping_address,
        [discount_info],
        shipping_price,
    )
    assert tax_rate == expected_tax_rate


def test_manager_get_order_shipping_tax_rate_sample_plugin(order_with_lines):
    order = order_with_lines
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    shipping_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))
    tax_rate = PluginsManager(plugins=plugins).get_order_shipping_tax_rate(
        order,
        shipping_price,
    )
    assert tax_rate == Decimal("0.08")


@pytest.mark.parametrize(
    "shipping_price, expected_tax_rate",
    [
        (TaxedMoney(Money(12, "USD"), Money(14, "USD")), Decimal("0.1667")),
        (Decimal("0.0"), Decimal("0.0")),
    ],
)
def test_manager_get_order_shipping_tax_rate_no_plugins(
    order_with_lines, shipping_price, expected_tax_rate
):
    order = order_with_lines
    tax_rate = PluginsManager(plugins=[]).get_order_shipping_tax_rate(
        order,
        shipping_price,
    )
    assert tax_rate == expected_tax_rate


@pytest.mark.parametrize(
    "plugins, total_line_price, quantity",
    [
        (
            ["saleor.plugins.tests.sample_plugins.PluginSample"],
            TaxedMoney(
                net=Money(amount=10, currency="USD"),
                gross=Money(amount=12, currency="USD"),
            ),
            2,
        ),
        (
            [],
            TaxedMoney(
                net=Money(amount=15, currency="USD"),
                gross=Money(amount=15, currency="USD"),
            ),
            1,
        ),
    ],
)
def test_manager_calculates_checkout_line_unit_price(
    plugins, total_line_price, quantity
):
    taxed_total = PluginsManager(plugins=plugins).calculate_checkout_line_unit_price(
        total_line_price, quantity
    )
    currency = total_line_price.net.currency
    expected_net = Money(
        amount=total_line_price.net.amount / quantity, currency=currency
    )
    expected_gross = Money(
        amount=total_line_price.gross.amount / quantity, currency=currency
    )
    assert TaxedMoney(net=expected_net, gross=expected_gross) == taxed_total


@pytest.mark.parametrize(
    "plugins, amount",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "12.30")],
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
            ["saleor.plugins.tests.sample_plugins.PluginSample"],
            [TaxType(code="123", description="abc")],
        ),
        ([], []),
    ],
)
def test_manager_uses_get_tax_rate_choices(plugins, tax_rate_list):
    assert tax_rate_list == PluginsManager(plugins=plugins).get_tax_rate_type_choices()


@pytest.mark.parametrize(
    "plugins, show_taxes",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], True), ([], False)],
)
def test_manager_show_taxes_on_storefront(plugins, show_taxes):
    assert show_taxes == PluginsManager(plugins=plugins).show_taxes_on_storefront()


@pytest.mark.parametrize(
    "plugins, price",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_product(product, plugins, price, channel_USD):
    country = Country("PL")
    variant = product.variants.all()[0]
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    currency = variant.get_price(
        variant.product, [], channel_USD, variant_channel_listing, None
    ).currency
    expected_price = Money(price, currency)
    taxed_price = PluginsManager(plugins=plugins).apply_taxes_to_product(
        product,
        variant.get_price(
            variant.product, [], channel_USD, variant_channel_listing, None
        ),
        country,
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price


@pytest.mark.parametrize(
    "plugins, price_amount",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_shipping(
    shipping_method, address, plugins, price_amount, channel_USD
):
    shipping_price = shipping_method.channel_listings.get(
        channel_id=channel_USD.id
    ).price
    expected_price = Money(price_amount, "USD")
    taxed_price = PluginsManager(plugins=plugins).apply_taxes_to_shipping(
        shipping_price, address
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price


@pytest.mark.parametrize(
    "plugins, amount",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "15.0"), ([], "0")],
)
def test_manager_get_tax_rate_percentage_value(plugins, amount, product):
    country = Country("PL")
    tax_rate_value = PluginsManager(plugins=plugins).get_tax_rate_percentage_value(
        product, country
    )
    assert tax_rate_value == Decimal(amount)


def test_manager_get_plugin_configurations(plugin_configuration):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    plugin_configs = manager._plugin_configs.values()
    assert len(plugin_configs) == 1
    assert set(plugin_configs) == set(list(PluginConfiguration.objects.all()))


def test_manager_get_plugin_configuration(plugin_configuration):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    plugin = manager.get_plugin(PluginSample.PLUGIN_ID)
    configuration_from_db = PluginConfiguration.objects.get(
        identifier=PluginSample.PLUGIN_ID
    )
    assert plugin.DEFAULT_CONFIGURATION == configuration_from_db.configuration


def test_manager_save_plugin_configuration(plugin_configuration):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    manager = PluginsManager(plugins=plugins)
    manager.save_plugin_configuration(PluginSample.PLUGIN_ID, {"active": False})
    plugin_configuration.refresh_from_db()
    assert not plugin_configuration.active


def test_plugin_updates_configuration_shape(
    new_config,
    new_config_structure,
    plugin_configuration,
    monkeypatch,
):

    config_structure = PluginSample.CONFIG_STRUCTURE.copy()
    config_structure["Foo"] = new_config_structure
    monkeypatch.setattr(PluginSample, "CONFIG_STRUCTURE", config_structure)

    monkeypatch.setattr(
        PluginSample,
        "DEFAULT_CONFIGURATION",
        plugin_configuration.configuration + [new_config],
    )

    manager = PluginsManager(
        plugins=["saleor.plugins.tests.sample_plugins.PluginSample"]
    )
    plugin = manager.get_plugin(PluginSample.PLUGIN_ID)

    assert len(plugin.configuration) == 5
    assert plugin.configuration[-1] == {**new_config, **new_config_structure}


def test_plugin_add_new_configuration(
    new_config,
    new_config_structure,
    monkeypatch,
):
    monkeypatch.setattr(PluginInactive, "DEFAULT_ACTIVE", True)
    monkeypatch.setattr(
        PluginInactive,
        "DEFAULT_CONFIGURATION",
        [new_config],
    )
    config_structure = {"Foo": new_config_structure}
    monkeypatch.setattr(PluginInactive, "CONFIG_STRUCTURE", config_structure)
    manager = PluginsManager(
        plugins=["saleor.plugins.tests.sample_plugins.PluginInactive"]
    )
    plugin = manager.get_plugin(PluginInactive.PLUGIN_ID)
    assert len(plugin.configuration) == 1
    assert plugin.configuration[0] == {**new_config, **new_config_structure}


def test_manager_serve_list_of_payment_gateways():
    expected_gateway = PaymentGateway(
        id=ActivePaymentGateway.PLUGIN_ID,
        name=ActivePaymentGateway.PLUGIN_NAME,
        config=ActivePaymentGateway.CLIENT_CONFIG,
        currencies=ActivePaymentGateway.SUPPORTED_CURRENCIES,
    )
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.ActivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.InactivePaymentGateway",
    ]
    manager = PluginsManager(plugins=plugins)
    assert manager.list_payment_gateways() == [expected_gateway]


def test_manager_serve_list_all_payment_gateways():
    expected_gateways = [
        PaymentGateway(
            id=ActivePaymentGateway.PLUGIN_ID,
            name=ActivePaymentGateway.PLUGIN_NAME,
            config=ActivePaymentGateway.CLIENT_CONFIG,
            currencies=ActivePaymentGateway.SUPPORTED_CURRENCIES,
        ),
        PaymentGateway(
            id=InactivePaymentGateway.PLUGIN_ID,
            name=InactivePaymentGateway.PLUGIN_NAME,
            config=[],
            currencies=[],
        ),
    ]

    plugins = [
        "saleor.plugins.tests.sample_plugins.ActivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.InactivePaymentGateway",
    ]
    manager = PluginsManager(plugins=plugins)
    assert manager.list_payment_gateways(active_only=False) == expected_gateways


def test_manager_serve_list_all_payment_gateways_specified_currency():
    expected_gateways = [
        PaymentGateway(
            id=ActiveDummyPaymentGateway.PLUGIN_ID,
            name=ActiveDummyPaymentGateway.PLUGIN_NAME,
            config=ActiveDummyPaymentGateway.CLIENT_CONFIG,
            currencies=ActiveDummyPaymentGateway.SUPPORTED_CURRENCIES,
        )
    ]

    plugins = [
        "saleor.plugins.tests.sample_plugins.ActivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.InactivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.ActiveDummyPaymentGateway",
    ]
    manager = PluginsManager(plugins=plugins)
    assert (
        manager.list_payment_gateways(currency="EUR", active_only=False)
        == expected_gateways
    )


def test_manager_serve_list_all_payment_gateways_specified_currency_two_gateways():
    expected_gateways = [
        PaymentGateway(
            id=ActivePaymentGateway.PLUGIN_ID,
            name=ActivePaymentGateway.PLUGIN_NAME,
            config=ActivePaymentGateway.CLIENT_CONFIG,
            currencies=ActivePaymentGateway.SUPPORTED_CURRENCIES,
        ),
        PaymentGateway(
            id=ActiveDummyPaymentGateway.PLUGIN_ID,
            name=ActiveDummyPaymentGateway.PLUGIN_NAME,
            config=ActiveDummyPaymentGateway.CLIENT_CONFIG,
            currencies=ActiveDummyPaymentGateway.SUPPORTED_CURRENCIES,
        ),
    ]

    plugins = [
        "saleor.plugins.tests.sample_plugins.ActivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.InactivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.ActiveDummyPaymentGateway",
    ]
    manager = PluginsManager(plugins=plugins)
    assert (
        manager.list_payment_gateways(currency="USD", active_only=False)
        == expected_gateways
    )


def test_manager_webhook(rf):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    plugin_path = "/webhook/paid"
    request = rf.post(path=f"/plugins/{PluginSample.PLUGIN_ID}{plugin_path}")

    response = manager.webhook(request, PluginSample.PLUGIN_ID)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert response.content.decode() == json.dumps({"received": True, "paid": True})


def test_manager_webhook_plugin_doesnt_have_webhook_support(rf):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)
    plugin_path = "/webhook/paid"
    request = rf.post(path=f"/plugins/{PluginInactive.PLUGIN_ID}{plugin_path}")
    response = manager.webhook(request, PluginSample.PLUGIN_ID)
    assert isinstance(response, HttpResponseNotFound)
    assert response.status_code == 404


def test_manager_inncorrect_plugin(rf):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    plugin_path = "/webhook/paid"
    request = rf.post(path=f"/plugins/incorrect.plugin.id{plugin_path}")
    response = manager.webhook(request, "incorrect.plugin.id")
    assert isinstance(response, HttpResponseNotFound)
    assert response.status_code == 404
