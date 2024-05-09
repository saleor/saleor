import json
from decimal import Decimal
from functools import partial
from unittest import mock
from unittest.mock import patch

import pytest
from django.http import HttpResponseNotFound, JsonResponse
from django.test import override_settings
from prices import Money, TaxedMoney

from ...channel import TransactionFlowStrategy
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.prices import quantize_price
from ...core.taxes import TaxType, zero_money, zero_taxed_money
from ...graphql.discount.utils import convert_migrated_sale_predicate_to_catalogue_info
from ...payment import TokenizedPaymentFlow
from ...payment.interface import (
    ListStoredPaymentMethodsRequestData,
    PaymentGateway,
    PaymentGatewayData,
    PaymentGatewayInitializeTokenizationRequestData,
    PaymentGatewayInitializeTokenizationResponseData,
    PaymentGatewayInitializeTokenizationResult,
    PaymentMethodInitializeTokenizationRequestData,
    PaymentMethodProcessTokenizationRequestData,
    PaymentMethodTokenizationResponseData,
    PaymentMethodTokenizationResult,
    StoredPaymentMethodRequestDeleteData,
    StoredPaymentMethodRequestDeleteResponseData,
    StoredPaymentMethodRequestDeleteResult,
    TransactionProcessActionData,
    TransactionSessionData,
    TransactionSessionResult,
)
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
    manager = get_plugins_manager(allow_replica=False)
    manager.get_all_plugins()
    assert isinstance(manager, PluginsManager)
    assert len(manager.all_plugins) == 1


def test_manager_with_default_configuration_for_channel_plugins(
    settings, channel_USD, channel_PLN
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.ChannelPluginSample",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager(allow_replica=False)
    manager.get_all_plugins()

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
    manager = get_plugins_manager(allow_replica=False)
    manager.get_all_plugins()

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
    manager = get_plugins_manager(allow_replica=False)

    plugins = manager.get_plugins(channel_slug=channel_USD.slug)

    assert plugins == manager.plugins_per_channel[channel_USD.slug]


def test_manager_get_active_plugins_with_channel_slug(
    settings, channel_USD, plugin_configuration, inactive_plugin_configuration
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager(allow_replica=False)

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
    manager = get_plugins_manager(allow_replica=False)

    plugins = manager.get_plugins(channel_slug=None)

    assert plugins == manager.all_plugins


def test_manager_get_active_plugins_without_channel_slug(
    settings, channel_USD, plugin_configuration, inactive_plugin_configuration
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = get_plugins_manager(allow_replica=False)

    plugins = manager.get_plugins(channel_slug=None, active_only=True)

    assert len(plugins) == 1
    assert isinstance(plugins[0], PluginSample)


@pytest.mark.parametrize(
    ("plugins", "total_amount"),
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_total(
    checkout_with_item_on_promotion, plugins, total_amount
):
    # given
    checkout = checkout_with_item_on_promotion
    currency = checkout.currency
    expected_total = Money(total_amount, currency)
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    taxed_total = manager.calculate_checkout_total(checkout_info, lines, None)

    # then
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    ("plugins", "subtotal_amount"),
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_subtotal(
    checkout_with_item_on_promotion, plugins, subtotal_amount
):
    # given
    checkout = checkout_with_item_on_promotion
    currency = checkout.currency
    expected_subtotal = Money(subtotal_amount, currency)
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    taxed_subtotal = PluginsManager(plugins=plugins).calculate_checkout_subtotal(
        checkout_info, lines, None
    )

    # then
    assert TaxedMoney(expected_subtotal, expected_subtotal) == taxed_subtotal


@pytest.mark.parametrize(
    ("plugins", "shipping_amount"),
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "0.0")],
)
def test_manager_calculates_checkout_shipping(
    checkout_with_item, plugins, shipping_amount
):
    currency = checkout_with_item.currency
    expected_shipping_price = Money(shipping_amount, currency)
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    taxed_shipping_price = PluginsManager(plugins=plugins).calculate_checkout_shipping(
        checkout_info, lines, None
    )
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    ("plugins", "shipping_amount"),
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "10.0")],
)
def test_manager_calculates_order_shipping(order_with_lines, plugins, shipping_amount):
    currency = order_with_lines.total.currency
    expected_shipping_price = Money(shipping_amount, currency)

    taxed_shipping_price = PluginsManager(plugins=plugins).calculate_order_shipping(
        order_with_lines, order_with_lines.lines.all()
    )
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    ("plugins", "amount"),
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_line_total(
    checkout_with_item_on_promotion, plugins, amount
):
    # given
    checkout = checkout_with_item_on_promotion
    currency = checkout.currency
    expected_total = Money(amount, currency)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    checkout_line_info = lines[0]

    # when
    taxed_total = PluginsManager(plugins=plugins).calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
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
            order_line.order,
            order_line,
            order_line.variant,
            order_line.variant.product,
            [order_line],
        )
        .price_with_discounts
    )
    assert expected_total == taxed_total


def test_manager_get_checkout_line_tax_rate_sample_plugin(checkout_with_item):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_line_info = lines[0]

    tax_rate = PluginsManager(plugins=plugins).get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        unit_price,
    )
    assert tax_rate == Decimal("0.08")


@pytest.mark.parametrize(
    ("unit_price", "expected_tax_rate"),
    [
        (TaxedMoney(Money(12, "USD"), Money(15, "USD")), Decimal("0.25")),
        (Decimal("0.0"), Decimal("0.0")),
    ],
)
def test_manager_get_checkout_line_tax_rate_no_plugins(
    checkout_with_item, unit_price, expected_tax_rate
):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_line_info = lines[0]
    tax_rate = PluginsManager(plugins=[]).get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
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
    ("unit_price", "expected_tax_rate"),
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


def test_manager_get_checkout_shipping_tax_rate_sample_plugin(checkout_with_item):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    shipping_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    tax_rate = PluginsManager(plugins=plugins).get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        shipping_price,
    )
    assert tax_rate == Decimal("0.08")


@pytest.mark.parametrize(
    ("shipping_price", "expected_tax_rate"),
    [
        (TaxedMoney(Money(12, "USD"), Money(14, "USD")), Decimal("0.1667")),
        (Decimal("0.0"), Decimal("0.0")),
    ],
)
def test_manager_get_checkout_shipping_tax_rate_no_plugins(
    checkout_with_item, shipping_price, expected_tax_rate
):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    tax_rate = PluginsManager(plugins=[]).get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
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
    ("shipping_price", "expected_tax_rate"),
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
    ("plugins", "total_line_price", "quantity"),
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
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_line_info = lines[0]

    taxed_total = PluginsManager(plugins=plugins).calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        address,
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
    ("plugins", "amount"),
    [(["saleor.plugins.tests.sample_plugins.PluginSample"], "1.0"), ([], "12.30")],
)
def test_manager_calculates_order_line(order_line, plugins, amount):
    variant = order_line.variant
    currency = order_line.unit_price.currency
    order = order_line.order
    expected_price = Money(amount, currency)
    unit_price = (
        PluginsManager(plugins=plugins)
        .calculate_order_line_unit(
            order_line.order, order_line, variant, variant.product, order.lines.all()
        )
        .price_with_discounts
    )
    assert expected_price == unit_price.gross


@pytest.mark.parametrize(
    ("plugins", "tax_rate_list"),
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
    ("plugins", "expected_tax_data"),
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
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    app_identifier = None
    assert PluginsManager(plugins=plugins).get_taxes_for_checkout(
        checkout_info, lines, app_identifier
    ) == expected_tax_data(checkout)


@pytest.mark.parametrize(
    ("plugins", "expected_tax_data"),
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
    app_identifier = None
    assert PluginsManager(plugins=plugins).get_taxes_for_order(
        order, app_identifier
    ) == expected_tax_data(order)


def test_manager_sale_created(promotion_converted_from_sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    promotion = promotion_converted_from_sale
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)
    promotion_returned, current_catalogue_returned = PluginsManager(
        plugins=plugins
    ).sale_created(promotion, current_catalogue)

    assert promotion == promotion_returned
    assert current_catalogue == current_catalogue_returned


def test_manager_sale_updated(promotion_converted_from_sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    promotion = promotion_converted_from_sale
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)
    (
        promotion_returned,
        previous_catalogue_returned,
        current_catalogue_returned,
    ) = PluginsManager(plugins=plugins).sale_updated(
        promotion, previous_catalogue, current_catalogue
    )

    assert promotion == promotion_returned
    assert current_catalogue == current_catalogue_returned
    assert previous_catalogue == previous_catalogue_returned


def test_manager_sale_deleted(promotion_converted_from_sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    promotion = promotion_converted_from_sale
    predicate = promotion.rules.first().catalogue_predicate
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    promotion_returned, previous_catalogue_returned = PluginsManager(
        plugins=plugins
    ).sale_created(promotion, previous_catalogue)

    assert promotion == promotion_returned
    assert previous_catalogue == previous_catalogue_returned


def test_manager_sale_toggle(promotion_converted_from_sale):
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    promotion = promotion_converted_from_sale
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    promotion_returned, current_catalogue_returned = PluginsManager(
        plugins=plugins
    ).sale_toggle(promotion, current_catalogue)

    assert promotion == promotion_returned
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

    response = manager.webhook(request, PluginSample.PLUGIN_ID, channel_slug=None)
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
    response = manager.webhook(request, PluginSample.PLUGIN_ID, channel_slug=None)
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
    response = manager.webhook(request, "incorrect.plugin.id", channel_slug=None)
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
        method_name="test_method", default_value=default_value, channel_slug=None
    )

    assert value == default_value


def test_run_method_on_plugins_default_value_when_not_existing_method_is_called(
    channel_USD, all_plugins_manager
):
    default_value = "default"
    value = all_plugins_manager._PluginsManager__run_method_on_plugins(
        method_name="test_method",
        default_value=default_value,
        channel_slug=channel_USD.slug,
    )

    assert value == default_value


def test_run_method_on_plugins_value_overridden_by_plugin_method(
    channel_USD, all_plugins_manager
):
    expected = ActiveDummyPaymentGateway.SUPPORTED_CURRENCIES  # last active plugin
    value = all_plugins_manager._PluginsManager__run_method_on_plugins(
        method_name="get_supported_currencies",
        default_value="default_value",
        channel_slug=channel_USD.slug,
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
        channel_slug=channel_USD.slug,
    )
    active_plugins_count = len(ACTIVE_PLUGINS)

    assert len(all_plugins_manager.all_plugins) == len(ALL_PLUGINS)
    assert (
        len([p for p in all_plugins_manager.all_plugins if p.active])
        == active_plugins_count
    )
    assert mocked_method.call_count == active_plugins_count

    called_plugins_id = [arg.args[0].PLUGIN_ID for arg in mocked_method.call_args_list]
    expected_active_plugins_id = [
        p.PLUGIN_ID
        for p in all_plugins_manager.plugins_per_channel[channel_USD.slug]
        if p.active
    ]

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

    plugins_manager.all_plugins = [usd_plugin_1, usd_plugin_2, pln_plugin]

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
    manager.get_all_plugins()
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
@mock.patch("saleor.plugins.manager.base_calculations.checkout_total")
def test_calculate_checkout_total_zero_default_value(
    mocked_base_checkout_total,
    mocked_run_method,
    checkout_with_item,
):
    # given
    plugins = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    currency = checkout_with_item.currency
    mocked_base_checkout_total.return_value = zero_money(currency)
    manager = PluginsManager(plugins=plugins)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    taxed_total = manager.calculate_checkout_total(checkout_info, lines, None)

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


def test_manager_payment_gateway_initialize_session(channel_USD, checkout):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    # when
    response = manager.payment_gateway_initialize_session(
        amount=Decimal("10.00"),
        payment_gateways=None,
        source_object=checkout,
    )

    # then
    assert isinstance(response, list)
    assert len(response) == 1


def test_manager_transaction_initialize_session(
    channel_USD, checkout, webhook_app, transaction_item_generator
):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        app=webhook_app,
        psp_reference=None,
        name=None,
        message=None,
    )
    action_type = TransactionFlowStrategy.CHARGE

    transaction_session_data = TransactionSessionData(
        transaction=transaction,
        source_object=checkout,
        action=TransactionProcessActionData(
            amount=Decimal("10"),
            currency=transaction.currency,
            action_type=action_type,
        ),
        customer_ip_address="127.0.0.1",
        payment_gateway_data=PaymentGatewayData(
            app_identifier=webhook_app.identifier, data=None, error=None
        ),
    )
    # when
    response = manager.transaction_initialize_session(
        transaction_session_data=transaction_session_data
    )

    # then
    assert isinstance(response, TransactionSessionResult)


def test_manager_transaction_process_session(
    channel_USD, checkout, webhook_app, transaction_item_generator
):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        app=webhook_app,
        psp_reference=None,
        name=None,
        message=None,
    )
    action_type = TransactionFlowStrategy.CHARGE

    transaction_session_data = TransactionSessionData(
        transaction=transaction,
        source_object=checkout,
        action=TransactionProcessActionData(
            amount=Decimal("10"),
            currency=transaction.currency,
            action_type=action_type,
        ),
        customer_ip_address="127.0.0.1",
        payment_gateway_data=PaymentGatewayData(
            app_identifier=webhook_app.identifier, data=None, error=None
        ),
    )
    # when
    response = manager.transaction_process_session(
        transaction_session_data=transaction_session_data
    )

    # then
    assert isinstance(response, TransactionSessionResult)


@patch("saleor.plugins.tests.sample_plugins.PluginSample.checkout_fully_paid")
def test_checkout_fully_paid(mocked_sample_method, checkout):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    # when
    manager.checkout_fully_paid(checkout)

    # then
    mocked_sample_method.assert_called_once_with(checkout, previous_value=None)


@patch("saleor.plugins.tests.sample_plugins.PluginSample.order_fully_refunded")
def test_order_fully_refunded(mocked_sample_method, order):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    # when
    manager.order_fully_refunded(order)

    # then
    mocked_sample_method.assert_called_once_with(order, previous_value=None)


@patch("saleor.plugins.tests.sample_plugins.PluginSample.order_refunded")
def test_order_refunded(mocked_sample_method, order):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    # when
    manager.order_refunded(order)

    # then
    mocked_sample_method.assert_called_once_with(order, previous_value=None)


@patch("saleor.plugins.tests.sample_plugins.PluginSample.order_paid")
def test_order_paid(mocked_sample_method, order):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    manager = PluginsManager(plugins=plugins)

    # when
    manager.order_paid(order)

    # then
    mocked_sample_method.assert_called_once_with(order, previous_value=None)


@patch("saleor.plugins.tests.sample_plugins.PluginSample.list_stored_payment_methods")
def test_list_stored_payment_methods(
    mocked_list_stored_payment_methods, channel_USD, customer_user
):
    # given
    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )

    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)

    # when
    manager.list_stored_payment_methods(data)

    # then
    mocked_list_stored_payment_methods.assert_called_once()


@patch(
    "saleor.plugins.tests.sample_plugins.PluginSample.stored_payment_method_request_delete"
)
def test_stored_payment_method_request_delete(
    mocked_stored_payment_method_request_delete, customer_user, channel_USD
):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user, payment_method_id="123", channel=channel_USD
    )
    previous_response = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
    )
    # when
    manager.stored_payment_method_request_delete(
        request_delete_data=request_delete_data
    )

    # then
    mocked_stored_payment_method_request_delete.assert_called_once_with(
        request_delete_data, previous_value=previous_response
    )


@patch(
    "saleor.plugins.tests.sample_plugins.PluginSample."
    "payment_gateway_initialize_tokenization"
)
def test_payment_gateway_initialize_tokenization(
    mocked_payment_gateway_initialize_tokenization, customer_user, channel_USD, app
):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    request_data = PaymentGatewayInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=app.identifier,
        channel=channel_USD,
        data={"data": "ABC"},
    )
    previous_response = PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER,
        error="Payment gateway initialize tokenization failed to deliver.",
        data=None,
    )

    # when
    manager.payment_gateway_initialize_tokenization(request_data=request_data)

    # then
    mocked_payment_gateway_initialize_tokenization.assert_called_once_with(
        request_data, previous_value=previous_response
    )


@patch(
    "saleor.plugins.tests.sample_plugins.PluginSample."
    "payment_method_initialize_tokenization"
)
def test_payment_method_initialize_tokenization(
    mocked_payment_method_initialize_tokenization, customer_user, channel_USD, app
):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)
    request_data = PaymentMethodInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=app.identifier,
        channel=channel_USD,
        data={"data": "ABC"},
        payment_flow_to_support=TokenizedPaymentFlow.INTERACTIVE,
    )
    previous_response = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method initialize tokenization failed to deliver.",
        data=None,
    )

    # when
    manager.payment_method_initialize_tokenization(request_data=request_data)

    # then
    mocked_payment_method_initialize_tokenization.assert_called_once_with(
        request_data, previous_value=previous_response
    )


@patch(
    "saleor.plugins.tests.sample_plugins.PluginSample."
    "payment_method_process_tokenization"
)
def test_payment_method_process_tokenization(
    mocked_payment_method_process_tokenization, customer_user, channel_USD, app
):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]
    manager = PluginsManager(plugins=plugins)

    expected_id = "test_id"

    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_id,
        channel=channel_USD,
        data={"data": "ABC"},
    )
    previous_response = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    # when
    manager.payment_method_process_tokenization(request_data=request_data)

    # then
    mocked_payment_method_process_tokenization.assert_called_once_with(
        request_data, previous_value=previous_response
    )


@pytest.mark.parametrize(
    ("allow_replica", "expected_connection_name"),
    [
        (True, "test replica"),
        (False, "test default"),
    ],
)
def test_plugin_manager_database(allow_replica, expected_connection_name):
    # given
    manager = PluginsManager(
        ["saleor.plugins.tests.sample_plugins.PluginSample"],
        allow_replica=allow_replica,
    )

    # when & then
    with override_settings(
        DATABASE_CONNECTION_REPLICA_NAME="test replica",
        DATABASE_CONNECTION_DEFAULT_NAME="test default",
    ):
        assert manager.database == expected_connection_name


def test_loaded_all_channels(channel_USD, channel_PLN, django_assert_num_queries):
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)

    # then
    with django_assert_num_queries(4):
        plugins = manager.get_all_plugins()
        assert plugins

    with django_assert_num_queries(0):
        plugins = manager.get_all_plugins()
        assert plugins


def test_get_plugin_invalid_channel():
    # given
    plugins = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    manager = PluginsManager(plugins=plugins)

    # when
    plugin = manager.get_plugin(
        "saleor.plugins.tests.sample_plugins.PluginSample", channel_slug="invalid"
    )

    # then
    assert plugin is None


@pytest.mark.parametrize(
    ("plugins", "calls"),
    [
        ([], 0),
        (["saleor.plugins.tests.sample_plugins.PluginInactive"], 0),
        (["saleor.plugins.tests.sample_plugins.PluginSample"], 1),
        (
            [
                "saleor.plugins.tests.sample_plugins.PluginInactive",
                "saleor.plugins.tests.sample_plugins.PluginSample",
            ],
            1,
        ),
    ],
)
def test_run_plugin_method_until_first_success_for_active_plugins_only(
    channel_USD, plugins, calls
):
    # given
    manager = PluginsManager(plugins=plugins)
    manager._ensure_channel_plugins_loaded(channel_slug=channel_USD.slug)

    # when
    with patch.object(
        PluginsManager,
        "_PluginsManager__run_method_on_single_plugin",
        return_value=None,
    ) as mock_run_method:
        result = manager._PluginsManager__run_plugin_method_until_first_success(
            "some_method", channel_slug=None
        )

    # then
    assert result is None
    assert mock_run_method.call_count == calls
