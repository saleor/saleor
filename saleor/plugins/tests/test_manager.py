import json
from decimal import Decimal
from functools import partial
from unittest import mock

import pytest
from django.http import HttpResponseNotFound, JsonResponse
from prices import Money, TaxedMoney

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.prices import quantize_price
from ...core.taxes import TaxType, zero_money, zero_taxed_money
from ...discount.utils import fetch_catalogue_info
from ...graphql.discount.mutations.utils import convert_catalogue_info_to_global_ids
from ...payment.interface import PaymentGateway
from ...product.models import Product
from ..base_plugin import ExternalAccessTokens
from ..manager import PluginsManager, get_plugins_manager
from ..models import PluginConfiguration
from ..tests.sample_plugins import (
    ACTIVE_PLUGINS,
    ALL_PLUGINS,
    ActiveDummyPaymentGateway,
    ActivePaymentGateway,
    ChannelPluginSample,
    InactivePaymentGateway,
    PluginInactive,
    PluginSample,
    sample_tax_data,
)


def test_get_plugins_manager(settings):
    plugin_path = "saleor.plugins.tests.sample_plugins.PluginSample"
    settings.PLUGINS = [plugin_path]
    manager = get_plugins_manager()
    assert isinstance(manager, PluginsManager)
    assert len(manager.all_plugins) == 1


def test_manager_with_default_configuration_for_channel_plugins(
    settings, channel_USD, channel_PLN
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.ChannelPluginSample",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager()
    assert len(manager.global_plugins) == 1
    assert isinstance(manager.global_plugins[0], PluginSample)
    assert {channel_PLN.slug, channel_USD.slug} == set(
        manager.plugins_per_channel.keys()
    )

    for channel_slug, plugins in manager.plugins_per_channel.items():
        assert len(plugins) == 2
        assert all(
            [
                isinstance(plugin, (PluginSample, ChannelPluginSample))
                for plugin in plugins
            ]
        )

    # global plugin + plugins for each channel
    assert len(manager.all_plugins) == 3


def test_manager_with_channel_plugins(
    settings, channel_USD, channel_PLN, channel_plugin_configurations
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.ChannelPluginSample",
    ]
    manager = get_plugins_manager()

    assert {channel_PLN.slug, channel_USD.slug} == set(
        manager.plugins_per_channel.keys()
    )

    for channel_slug, plugins in manager.plugins_per_channel.items():
        assert len(plugins) == 1
        # make sure that we load proper config from DB
        assert plugins[0].configuration[0]["value"] == channel_slug

    # global plugin + plugins for each channel
    assert len(manager.all_plugins) == 2


def test_manager_get_plugins_with_channel_slug(
    settings, channel_USD, plugin_configuration, inactive_plugin_configuration
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager()

    plugins = manager.get_plugins(channel_slug=channel_USD.slug)

    assert plugins == manager.plugins_per_channel[channel_USD.slug]


def test_manager_get_active_plugins_with_channel_slug(
    settings, channel_USD, plugin_configuration, inactive_plugin_configuration
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager()

    plugins = manager.get_plugins(channel_slug=channel_USD.slug, active_only=True)

    assert len(plugins) == 1
    assert isinstance(plugins[0], PluginSample)


def test_manager_get_plugins_without_channel_slug(
    settings, channel_USD, plugin_configuration, inactive_plugin_configuration
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager()

    plugins = manager.get_plugins(channel_slug=None)

    assert plugins == manager.all_plugins


def test_manager_get_active_plugins_without_channel_slug(
    settings, channel_USD, plugin_configuration, inactive_plugin_configuration
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager()

    plugins = manager.get_plugins(channel_slug=None, active_only=True)

    assert len(plugins) == 1
    assert isinstance(plugins[0], PluginSample)


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
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    taxed_total = manager.calculate_checkout_total(
        checkout_info, lines, None, [discount_info]
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
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    taxed_subtotal = PluginsManager(plugins=plugins).calculate_checkout_subtotal(
        checkout_info, lines, None, [discount_info]
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
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    taxed_shipping_price = PluginsManager(plugins=plugins).calculate_checkout_shipping(
        checkout_info, lines, None, [discount_info]
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
    currency = checkout_with_item.currency
    expected_total = Money(amount, currency)
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    checkout_line_info = lines[0]
    taxed_total = PluginsManager(plugins=plugins).calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [discount_info],
    )
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins",
    [["saleor.plugins.tests.sample_plugins.PluginSample"], []],
)
def test_manager_calculates_order_line_total(order_line, plugins):
    currency = order_line.order.currency
    expected_total = (
        TaxedMoney(Money("1.0", currency), Money("1.0", currency))
        if plugins
        else quantize_price(
            TaxedMoney(order_line.base_unit_price, order_line.base_unit_price)
            * order_line.quantity,
            currency,
        )
    )
    taxed_total = (
        PluginsManager(plugins=plugins)
        .calculate_order_line_total(
            order_line.order, order_line, order_line.variant, order_line.variant.product
        )
        .price_with_discounts
    )
    assert expected_total == taxed_total


def test_manager_get_checkout_line_tax_rate_sample_plugin(
    checkout_with_item, discount_info
):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    checkout_line_info = lines[0]

    tax_rate = PluginsManager(plugins=plugins).get_checkout_line_tax_rate(
        checkout_info,
        lines,
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
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    checkout_line_info = lines[0]
    tax_rate = PluginsManager(plugins=[]).get_checkout_line_tax_rate(
        checkout_info,
        lines,
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
        line.variant,
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
        line.variant,
        None,
        unit_price,
    )
    assert tax_rate == expected_tax_rate


def test_manager_get_checkout_shipping_tax_rate_sample_plugin(
    checkout_with_item, discount_info
):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    shipping_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )

    tax_rate = PluginsManager(plugins=plugins).get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
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
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )

    tax_rate = PluginsManager(plugins=[]).get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
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
                gross=Money(amount=10, currency="USD"),
            ),
            1,
        ),
        (
            [],
            TaxedMoney(
                net=Money(amount=20, currency="USD"),
                gross=Money(amount=20, currency="USD"),
            ),
            2,
        ),
    ],
)
def test_manager_calculates_checkout_line_unit_price(
    plugins, total_line_price, quantity, checkout_with_item, address
):
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    checkout_line_info = lines[0]

    taxed_total = PluginsManager(plugins=plugins).calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        [],
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
    variant = order_line.variant
    currency = order_line.unit_price.currency
    expected_price = Money(amount, currency)
    unit_price = (
        PluginsManager(plugins=plugins)
        .calculate_order_line_unit(
            order_line.order, order_line, variant, variant.product
        )
        .price_with_discounts
    )
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


def sample_none_data(obj):
    return None


@pytest.mark.parametrize(
    "plugins, show_taxes",
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], True), ([], False)],
)
def test_manager_show_taxes_on_storefront(plugins, show_taxes):
    assert show_taxes == PluginsManager(plugins=plugins).show_taxes_on_storefront()


@pytest.mark.parametrize(
    "plugins, expected_tax_data",
    [
        ([], sample_none_data),
        (["saleor.plugins.tests.sample_plugins.PluginSample"], sample_tax_data),
    ],
)
def test_manager_get_taxes_for_checkout(
    checkout,
    plugins,
    expected_tax_data,
):
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    assert PluginsManager(plugins=plugins).get_taxes_for_checkout(
        checkout_info, lines
    ) == expected_tax_data(checkout)


@pytest.mark.parametrize(
    "plugins, expected_tax_data",
    [
        ([], sample_none_data),
        (["saleor.plugins.tests.sample_plugins.PluginSample"], sample_tax_data),
    ],
)
def test_manager_get_taxes_for_order(
    order,
    plugins,
    expected_tax_data,
):
    assert PluginsManager(plugins=plugins).get_taxes_for_order(
        order
    ) == expected_tax_data(order)


def test_manager_sale_created(sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    sale_returned, current_catalogue_returned = PluginsManager(
        plugins=plugins
    ).sale_created(sale, current_catalogue)

    assert sale == sale_returned
    assert current_catalogue == current_catalogue_returned


def test_manager_sale_updated(sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    (
        sale_returned,
        previous_catalogue_returned,
        current_catalogue_returned,
    ) = PluginsManager(plugins=plugins).sale_updated(
        sale, previous_catalogue, current_catalogue
    )

    assert sale == sale_returned
    assert current_catalogue == current_catalogue_returned
    assert previous_catalogue == previous_catalogue_returned


def test_manager_sale_deleted(sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    sale_returned, previous_catalogue_returned = PluginsManager(
        plugins=plugins
    ).sale_created(sale, previous_catalogue)

    assert sale == sale_returned
    assert previous_catalogue == previous_catalogue_returned


def test_manager_sale_toggle(sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    sale_returned, current_catalogue_returned = PluginsManager(
        plugins=plugins
    ).sale_toggle(sale, current_catalogue)

    assert sale == sale_returned
    assert current_catalogue == current_catalogue_returned


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
    manager.save_plugin_configuration(PluginSample.PLUGIN_ID, None, {"active": False})
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


def test_manager_serve_list_of_payment_gateways(channel_USD):
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


def test_manager_serve_list_all_payment_gateways(channel_USD):
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


def test_manager_serve_list_all_payment_gateways_specified_currency(channel_USD):
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


def test_manager_serve_list_all_payment_gateways_specified_currency_two_gateways(
    channel_USD,
):
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


def test_manager_external_authentication(rf):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)

    response = manager.external_authentication_url(
        PluginSample.PLUGIN_ID, {"redirectUrl": "ABC"}, rf.request()
    )
    assert response == {"authorizeUrl": "http://www.auth.provider.com/authorize/"}


def test_manager_external_refresh(rf):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)
    response = manager.external_refresh(
        PluginSample.PLUGIN_ID, {"refreshToken": "ABC11"}, rf.request()
    )

    expected_plugin_response = ExternalAccessTokens(
        token="token4", refresh_token="refresh5", csrf_token="csrf6"
    )
    assert response == expected_plugin_response


def test_manager_external_obtain_access_tokens(rf):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)
    response = manager.external_obtain_access_tokens(
        PluginSample.PLUGIN_ID, {"code": "ABC11", "state": "state1"}, rf.request()
    )

    expected_plugin_response = ExternalAccessTokens(
        token="token1", refresh_token="refresh2", csrf_token="csrf3"
    )
    assert response == expected_plugin_response


def test_manager_authenticate_user(rf, admin_user):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)
    user = manager.authenticate_user(rf.request())
    assert user == admin_user


def test_manager_external_logout(rf, admin_user):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)
    response = manager.external_logout(PluginSample.PLUGIN_ID, {}, rf.request())
    assert response == {"logoutUrl": "http://www.auth.provider.com/logout/"}


def test_manager_external_verify(rf, admin_user):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)
    user, response_data = manager.external_verify(
        PluginSample.PLUGIN_ID, {}, rf.request()
    )
    assert user == admin_user
    assert response_data == {"some_data": "data"}


def test_list_external_authentications(channel_USD):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.ActivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)
    external_auths = manager.list_external_authentications(active_only=False)

    assert {
        "id": PluginInactive.PLUGIN_ID,
        "name": PluginInactive.PLUGIN_NAME,
    } in external_auths
    assert {
        "id": PluginSample.PLUGIN_ID,
        "name": PluginSample.PLUGIN_NAME,
    } in external_auths


def test_list_external_authentications_active_only(channel_USD):
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.ActivePaymentGateway",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]

    manager = PluginsManager(plugins=plugins)
    external_auths = manager.list_external_authentications(active_only=True)

    assert {
        "id": PluginSample.PLUGIN_ID,
        "name": PluginSample.PLUGIN_NAME,
    } in external_auths


def test_run_method_on_plugins_default_value(plugins_manager):
    default_value = "default"
    value = plugins_manager._PluginsManager__run_method_on_plugins(
        method_name="test_method",
        default_value=default_value,
    )

    assert value == default_value


def test_run_method_on_plugins_default_value_when_not_existing_method_is_called(
    channel_USD, all_plugins_manager
):
    default_value = "default"
    value = all_plugins_manager._PluginsManager__run_method_on_plugins(
        method_name="test_method",
        default_value=default_value,
    )

    assert value == default_value


def test_run_method_on_plugins_value_overridden_by_plugin_method(
    channel_USD, all_plugins_manager
):
    expected = ActiveDummyPaymentGateway.SUPPORTED_CURRENCIES  # last active plugin
    value = all_plugins_manager._PluginsManager__run_method_on_plugins(
        method_name="get_supported_currencies",
        default_value="default_value",
    )

    assert value == expected


@mock.patch(
    "saleor.plugins.manager.PluginsManager._PluginsManager__run_method_on_single_plugin"
)
def test_run_method_on_plugins_only_on_active_ones(
    mocked_method, channel_USD, all_plugins_manager
):
    all_plugins_manager._PluginsManager__run_method_on_plugins(
        method_name="test_method_name",
        default_value="default_value",
    )
    active_plugins_count = len(ACTIVE_PLUGINS)

    assert len(all_plugins_manager.all_plugins) == len(ALL_PLUGINS)
    assert (
        len([p for p in all_plugins_manager.all_plugins if p.active])
        == active_plugins_count
    )
    assert mocked_method.call_count == active_plugins_count

    called_plugins_id = [arg.args[0].PLUGIN_ID for arg in mocked_method.call_args_list]
    expected_active_plugins_id = [p.PLUGIN_ID for p in ACTIVE_PLUGINS]

    assert called_plugins_id == expected_active_plugins_id


@mock.patch(
    "saleor.plugins.manager.PluginsManager._PluginsManager__run_method_on_single_plugin"
)
def test_run_method_on_plugins_only_for_given_channel(
    mocked_run_on_single_plugin, plugins_manager, channel_USD, channel_PLN
):
    # given
    default_value = "default"

    usd_plugin_1 = ActiveDummyPaymentGateway(
        active=True, channel=channel_USD, configuration=[]
    )
    usd_plugin_2 = ActivePaymentGateway(
        active=True, channel=channel_USD, configuration=[]
    )
    pln_plugin = ChannelPluginSample(active=True, channel=channel_PLN, configuration=[])

    plugins_manager.plugins = [usd_plugin_1, usd_plugin_2, pln_plugin]

    plugins_manager.plugins_per_channel[channel_USD.slug] = [usd_plugin_1, usd_plugin_2]
    plugins_manager.plugins_per_channel[channel_PLN.slug] = [pln_plugin]

    # when
    plugins_manager._PluginsManager__run_method_on_plugins(
        method_name="test_method",
        default_value=default_value,
        channel_slug=channel_USD.slug,
    )

    # then
    assert mocked_run_on_single_plugin.call_count == 2
    called_plugins_id = {
        arg.args[0].PLUGIN_ID for arg in mocked_run_on_single_plugin.call_args_list
    }
    assert called_plugins_id == {usd_plugin_1.PLUGIN_ID, usd_plugin_2.PLUGIN_ID}


def test_run_method_on_single_plugin_method_does_not_exist(plugins_manager):
    default_value = "default_value"
    method_name = "method_does_not_exist"
    plugin = ActivePaymentGateway

    assert (
        plugins_manager._PluginsManager__run_method_on_single_plugin(
            plugin, method_name, default_value
        )
        == default_value
    )


def test_run_method_on_single_plugin_method_not_implemented(plugins_manager):
    default_value = "default_value"
    plugin = ChannelPluginSample(configuration=None, active=True)
    method_name = ChannelPluginSample.sample_not_implemented.__name__

    assert (
        plugins_manager._PluginsManager__run_method_on_single_plugin(
            plugin, method_name, default_value
        )
        == default_value
    )


def test_run_method_on_single_plugin_valid_response(plugins_manager):
    default_value = "default_value"
    plugin = ActiveDummyPaymentGateway(configuration=None, active=True)
    method_name = ActivePaymentGateway.get_supported_currencies.__name__

    assert (
        plugins_manager._PluginsManager__run_method_on_single_plugin(
            plugin, method_name, default_value
        )
        == plugin.SUPPORTED_CURRENCIES
    )


def test_run_check_payment_balance(channel_USD):
    plugins = ["saleor.plugins.tests.sample_plugins.ActiveDummyPaymentGateway"]

    manager = PluginsManager(plugins=plugins)
    assert manager.check_payment_balance({}, "main") == {"test_response": "success"}


def test_run_check_payment_balance_not_implemented(channel_USD):
    plugins = ["saleor.plugins.tests.sample_plugins.ActivePlugin"]

    manager = PluginsManager(plugins=plugins)
    assert not manager.check_payment_balance({}, "main")


def test_create_plugin_manager_initializes_requestor_lazily(channel_USD):
    def fake_request_getter(mock):
        return mock()

    user_mock = mock.MagicMock()
    user_mock.return_value.id = "some id"
    user_mock.return_value.name = "some name"

    plugins = ["saleor.plugins.tests.sample_plugins.ActivePlugin"]

    manager = PluginsManager(
        plugins=plugins, requestor_getter=partial(fake_request_getter, user_mock)
    )
    user_mock.assert_not_called()

    plugin = manager.all_plugins.pop()

    assert plugin.requestor.id == "some id"
    assert plugin.requestor.name == "some name"

    user_mock.assert_called_once()


def test_manager_delivery_retry(event_delivery):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    manager = PluginsManager(plugins=plugins)
    delivery_retry = manager.event_delivery_retry(event_delivery=event_delivery)
    assert delivery_retry


@mock.patch(
    "saleor.plugins.manager.PluginsManager._PluginsManager__run_method_on_single_plugin"
)
@mock.patch("saleor.plugins.manager.base_calculations.base_checkout_total")
def test_calculate_checkout_total_zero_default_value(
    mocked_base_checkout_total,
    mocked_run_method,
    checkout_with_item,
    discount_info,
):
    # given
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    currency = checkout_with_item.currency
    mocked_base_checkout_total.return_value = zero_money(currency)
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )

    # when
    taxed_total = manager.calculate_checkout_total(
        checkout_info, lines, None, [discount_info]
    )

    # then
    assert "calculate_checkout_total" not in mocked_run_method.call_args_list
    assert taxed_total == zero_taxed_money(currency)


def test_manager_is_event_active_for_any_plugin_with_inactive_plugin(channel_USD):
    # given
    plugins = ["saleor.plugins.tests.sample_plugins.PluginInactive"]

    manager = PluginsManager(plugins=plugins)

    # when & then
    assert not manager.is_event_active_for_any_plugin(
        "authenticate_user", channel_USD.slug
    )


def test_manager_is_event_active_for_any_plugin(channel_USD):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    # when & then
    assert manager.is_event_active_for_any_plugin(
        "calculate_checkout_total", channel_USD.slug
    )
