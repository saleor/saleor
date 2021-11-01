import json
import uuid
from decimal import Decimal
from typing import List
from unittest import mock

import graphene
import pytest

from ....app.models import App
from ....graphql.tests.utils import get_graphql_content
from ....webhook.event_types import WebhookEventType
from ....webhook.models import Webhook, WebhookEvent
from ....webhook.payloads import (
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
)
from ...base_plugin import ExcludedShippingMethod, ShippingMethod
from ...manager import get_plugins_manager
from ..tasks import trigger_webhook_sync
from ..utils import (
    parse_excluded_shipping_methods_response,
    parse_list_shipping_methods_response,
)


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


@pytest.fixture()
def available_shipping_methods_factory():
    def factory(num_methods=1) -> List[ShippingMethod]:
        methods = []
        for i in range(num_methods):
            methods.append(
                ShippingMethod(
                    id=str(i),
                    price=Decimal("10.0"),
                    name=uuid.uuid4().hex,
                    maximum_order_weight=Decimal("0"),
                    minimum_order_weight=Decimal("100"),
                    maximum_delivery_days=0,
                    minimum_delivery_days=5,
                )
            )
        return methods

    return factory


ORDER_QUERY_SHIPPING_METHOD = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    shippingMethods {
                        id
                        name
                        active
                        message
                    }
                    availableShippingMethods {
                        id
                        name
                        active
                        message
                    }
                }
            }
        }
    }
"""

CHECKOUT_QUERY_SHIPPING_METHOD = """
    query CheckoutsQuery {
        checkouts(first: 1) {
            edges {
                node {
                    shippingMethods {
                        id
                        name
                        active
                    }
                    availableShippingMethods {
                        id
                        name
                        active
                    }
                }
            }
        }
    }
"""


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, shipping_app):
    data = {"key": "value"}
    trigger_webhook_sync(
        WebhookEventType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, data, shipping_app
    )
    webhook = shipping_app.webhooks.first()
    mock_request.assert_called_once_with(
        shipping_app.name,
        webhook.target_url,
        webhook.secret_key,
        WebhookEventType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        data,
    )


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


@pytest.fixture
def shipping_app(db, permission_manage_orders, permission_manage_checkouts):
    app = App.objects.create(name="Shipping App", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_checkouts)

    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-gateway.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(
                event_type=WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS,
                webhook=webhook,
            ),
            WebhookEvent(
                event_type=WebhookEventType.ORDER_FILTER_SHIPPING_METHODS,
                webhook=webhook,
            ),
        ]
    )
    return app


@mock.patch("saleor.plugins.webhook.plugin.send_webhook_request_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin.generate_excluded_shipping_methods_for_order_payload"
)
def test_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
    shipping_app,
):
    # given
    webhook_reason = "spanish-inquisition"
    other_reason = "it's a trap"
    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = [
        ExcludedShippingMethod(id="1", reason=other_reason),
        ExcludedShippingMethod(id="2", reason=other_reason),
    ]

    # when
    excluded_methods = plugin.excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        previous_value=previous_value,
    )
    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert other_reason in em.reason
    mocked_webhook.assert_called_once_with(
        shipping_app.name,
        mock.ANY,
        mock.ANY,
        WebhookEventType.ORDER_FILTER_SHIPPING_METHODS,
        payload,
    )


def test_parse_excluded_shipping_methods_response():
    # given
    response = {
        "excluded_methods": [
            {
                "id": "",
            },
            {
                "id": "not-an-id",
            },
            {
                "id": graphene.Node.to_global_id("Car", "1"),
            },
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "2"),
            },
        ]
    }
    # when
    excluded_methods = parse_excluded_shipping_methods_response(response)
    # then
    assert len(excluded_methods) == 1
    assert excluded_methods[0].id == "2"


@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_order"
)
def test_order_shipping_methods(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = order_with_lines.shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)
    ]
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    # when
    response = staff_api_client.post_graphql(ORDER_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    shipping_methods = order_data["shippingMethods"]
    # then
    assert len(shipping_methods) == 1
    assert not shipping_methods[0]["active"]
    assert shipping_methods[0]["message"] == webhook_reason


@pytest.mark.parametrize(
    "webhook_response, expected_count",
    [(lambda s: [ExcludedShippingMethod(s.id, "")], 0), (lambda s: [], 1)],
)
@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_order"
)
def test_order_available_shipping_methods(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    settings,
    webhook_response,
    expected_count,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_webhook.side_effect = lambda *args, **kwargs: webhook_response(
        order_with_lines.shipping_method
    )
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    # when
    response = staff_api_client.post_graphql(ORDER_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    # then
    assert len(order_data["availableShippingMethods"]) == expected_count


@mock.patch("saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_order")
def test_order_shipping_methods_webhook_called_once(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
):
    # given
    mocked_webhook.side_effect = [[], AssertionError("called twice.")]
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    # when
    response = staff_api_client.post_graphql(ORDER_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    # then
    assert len(order_data["availableShippingMethods"]) == 1
    assert len(order_data["shippingMethods"]) == 1


@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_methods(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = checkout_ready_to_complete.shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)
    ]
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(CHECKOUT_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    checkout_data = content["data"]["checkouts"]["edges"][0]["node"]

    shipping_methods = checkout_data["shippingMethods"]
    # then
    assert len(shipping_methods) == 2
    inactive_method = list(
        filter(
            lambda s: s["id"]
            == graphene.Node.to_global_id(
                "ShippingMethod", excluded_shipping_method_id
            ),
            shipping_methods,
        )
    )
    assert not inactive_method[0]["active"]


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_available_shipping_methods(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"

    excluded_shipping_method_id = checkout_ready_to_complete.shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)
    ]

    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(CHECKOUT_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    shipping_methods = content["data"]["checkouts"]["edges"][0]["node"][
        "availableShippingMethods"
    ]
    # then
    assert len(shipping_methods) == 1
    assert shipping_methods[0]["active"]


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_methods_webhook_called_once(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
):
    # given
    mocked_webhook.side_effect = [[], AssertionError("called twice.")]
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(CHECKOUT_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    checkout_data = content["data"]["checkouts"]["edges"][0]["node"]
    # then
    assert len(checkout_data["availableShippingMethods"]) == 2
    assert len(checkout_data["shippingMethods"]) == 2


@mock.patch("saleor.plugins.webhook.plugin.send_webhook_request_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin."
    "generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    shipping_app,
):
    # given
    webhook_reason = "spanish-inquisition"
    other_reason = "it's a trap"
    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = [
        ExcludedShippingMethod(id="1", reason=other_reason),
        ExcludedShippingMethod(id="2", reason=other_reason),
    ]
    # when
    excluded_methods = plugin.excluded_shipping_methods_for_checkout(
        checkout=checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        previous_value=previous_value,
    )
    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert other_reason in em.reason
    mocked_webhook.assert_called_once_with(
        shipping_app.name,
        mock.ANY,
        mock.ANY,
        WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS,
        payload,
    )


def test_generate_excluded_shipping_methods_for_order_payload(
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
):
    # given
    methods = available_shipping_methods_factory(num_methods=3)
    # when
    json_payload = json.loads(
        generate_excluded_shipping_methods_for_order_payload(
            order=order_with_lines, available_shipping_methods=methods
        )
    )
    # then
    assert len(json_payload["shipping_methods"]) == 3
    assert json_payload["shipping_methods"][0]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[0].id
    )
    assert json_payload["shipping_methods"][1]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[1].id
    )
    assert json_payload["shipping_methods"][2]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[2].id
    )
    graphql_order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    assert json_payload["order"]["id"] == graphql_order_id


def test_generate_excluded_shipping_methods_for_checkout_payload(
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
):
    # given
    methods = available_shipping_methods_factory(num_methods=3)
    # when
    json_payload = json.loads(
        generate_excluded_shipping_methods_for_checkout_payload(
            checkout=checkout_with_items, available_shipping_methods=methods
        )
    )
    # then
    assert len(json_payload["shipping_methods"]) == 3
    assert json_payload["shipping_methods"][0]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[0].id
    )
    assert json_payload["shipping_methods"][1]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[1].id
    )
    assert json_payload["shipping_methods"][2]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[2].id
    )
    assert "checkout" in json_payload
    assert "channel" in json_payload["checkout"]
