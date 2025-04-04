from unittest.mock import patch

import pytest

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.taxes import TaxDataError
from ..manager import PluginsManager, get_plugins_manager
from ..tests.sample_plugins import sample_tax_data


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
    # given
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    app_identifier = None

    # when
    tax_data = PluginsManager(plugins=plugins).get_taxes_for_checkout(
        checkout_info, lines, app_identifier
    )

    # then
    assert tax_data == expected_tax_data(checkout)


@patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.get_taxes_for_checkout",
    side_effect=TaxDataError("test error"),
)
def test_manager_get_taxes_for_checkout_raises_error(
    mocked_get_taxes_for_checkout,
    checkout,
):
    # given
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    app_identifier = None
    plugins = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    # when & then
    with pytest.raises(TaxDataError):
        PluginsManager(plugins=plugins).get_taxes_for_checkout(
            checkout_info, lines, app_identifier
        )

    mocked_get_taxes_for_checkout.assert_called_once()


def test_manager_get_taxes_for_checkout_raises_no_active_plugin(
    checkout,
):
    # given
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    app_identifier = None

    # when
    tax_data = PluginsManager(plugins=[]).get_taxes_for_checkout(
        checkout_info, lines, app_identifier
    )

    # then
    assert tax_data is None


@pytest.mark.parametrize(
    "plugins",
    [
        # first plugin that raises an error
        [
            "saleor.plugins.webhook.plugin.WebhookPlugin",
            "saleor.plugins.tests.sample_plugins.PluginSample",
        ],
        # as a second plugin that raises an error
        [
            "saleor.plugins.tests.sample_plugins.PluginSample",
            "saleor.plugins.webhook.plugin.WebhookPlugin",
        ],
    ],
)
@patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.get_taxes_for_checkout",
    side_effect=TaxDataError("test error"),
)
def test_manager_get_taxes_for_checkout_multiple_plugins(
    mocked_get_taxes_for_checkout,
    plugins,
    checkout,
):
    # given
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    app_identifier = None

    # when
    tax_data = PluginsManager(plugins).get_taxes_for_checkout(
        checkout_info, lines, app_identifier
    )

    # then
    assert tax_data == sample_tax_data(checkout)


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
    # given
    app_identifier = None

    # when
    tax_data = PluginsManager(plugins=plugins).get_taxes_for_order(
        order, app_identifier
    )

    # then
    assert tax_data == expected_tax_data(order)


@patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.get_taxes_for_order",
    side_effect=TaxDataError("test error"),
)
def test_manager_get_taxes_for_order_raises_error(
    mocked_get_taxes_for_order,
    order,
):
    # given
    app_identifier = None
    plugins = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    # when & then
    with pytest.raises(TaxDataError):
        PluginsManager(plugins=plugins).get_taxes_for_order(order, app_identifier)

    mocked_get_taxes_for_order.assert_called_once()


def test_manager_get_taxes_for_order_raises_no_active_plugin(
    order,
):
    # given
    app_identifier = None

    # when
    tax_data = PluginsManager(plugins=[]).get_taxes_for_order(order, app_identifier)

    # then
    assert tax_data is None


@pytest.mark.parametrize(
    "plugins",
    [
        # first plugin that raises an error
        [
            "saleor.plugins.webhook.plugin.WebhookPlugin",
            "saleor.plugins.tests.sample_plugins.PluginSample",
        ],
        # as a second plugin that raises an error
        [
            "saleor.plugins.tests.sample_plugins.PluginSample",
            "saleor.plugins.webhook.plugin.WebhookPlugin",
        ],
    ],
)
@patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.get_taxes_for_order",
    side_effect=TaxDataError("test error"),
)
def test_manager_get_taxes_for_order_multiple_plugins(
    mocked_get_taxes_for_order,
    plugins,
    order,
):
    # given
    app_identifier = None

    # when
    tax_data = PluginsManager(plugins).get_taxes_for_order(order, app_identifier)

    # then
    assert tax_data == sample_tax_data(order)
