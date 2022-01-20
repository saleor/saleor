from unittest import mock

import graphene
import pytest

from ....core.models import EventDelivery
from ....webhook.event_types import WebhookEventSyncType
from ...manager import get_plugins_manager
from ..tasks import trigger_webhook_sync
from ..utils import parse_list_shipping_methods_response


@pytest.fixture
def plugin_manager(settings, channel_USD):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    return manager


@pytest.fixture
def webhook_plugin(plugin_manager):
    def factory():
        return plugin_manager.global_plugins[0]

    return factory


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, shipping_app):
    data = '{"key": "value"}'
    trigger_webhook_sync(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, data, shipping_app
    )
    event_delivery = EventDelivery.objects.first()
    mock_request.assert_called_once_with(shipping_app.name, event_delivery)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout(
    mock_send_request, shipping_app, webhook_plugin, checkout
):
    plugin = webhook_plugin()
    mock_json_response = [
        {
            "id": "shipping_method_id",
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response
    methods = plugin.get_shipping_methods_for_checkout(checkout, None)
    expected_methods = parse_list_shipping_methods_response(
        mock_json_response, shipping_app
    )

    assert len(methods) == 1
    assert methods[0] == expected_methods[0]


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_shipping_method(mock_send_request, shipping_app, plugin_manager, checkout):
    response_method_id = "abcd"
    shipping_method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        },
        {
            "id": "cdef",
            "name": "Provider - Priority",
            "amount": "15",
            "currency": "USD",
            "maximum_delivery_days": None,
        },
    ]
    mock_send_request.return_value = mock_json_response
    shipping_method = plugin_manager.get_shipping_method(
        shipping_method_id, checkout, None
    )

    assert shipping_method.id == shipping_method_id


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_shipping_method_empty_response(
    mock_send_request, shipping_app, plugin_manager, checkout
):
    shipping_method_id = graphene.Node.to_global_id("app", f"{shipping_app.id}:abcd")
    mock_send_request.return_value = []
    shipping_method = plugin_manager.get_shipping_method(
        shipping_method_id, checkout, None
    )

    assert shipping_method is None
