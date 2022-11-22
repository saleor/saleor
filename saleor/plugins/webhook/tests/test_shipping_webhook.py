import json
from unittest import mock

import graphene
import pytest

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core.models import EventDelivery
from ....graphql.tests.utils import get_graphql_content
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.payloads import (
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
)
from ...base_plugin import ExcludedShippingMethod
from ...manager import get_plugins_manager
from ..const import (
    CACHE_EXCLUDED_SHIPPING_KEY,
    CACHE_EXCLUDED_SHIPPING_TIME,
    EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
)
from ..shipping import get_excluded_shipping_methods_from_response, to_shipping_app_id
from ..tasks import trigger_webhook_sync

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


@mock.patch("saleor.plugins.webhook.shipping.cache.set")
@mock.patch("saleor.plugins.webhook.shipping.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin.generate_excluded_shipping_methods_for_order_payload"
)
def test_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
    shipping_app_factory,
):
    # given
    shipping_app = shipping_app_factory()
    webhook_reason = "Order contains dangerous products."
    other_reason = "Shipping is not applicable for this order."

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
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    mocked_webhook.assert_called_once_with(
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        payload,
        shipping_app.webhooks.get(events__event_type=event_type),
        subscribable_object=order_with_lines,
        timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
    )
    expected_cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(order_with_lines.id)

    expected_excluded_shipping_method = [{"id": "1", "reason": webhook_reason}]

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        (payload, expected_excluded_shipping_method),
        CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.plugins.webhook.shipping.cache.set")
@mock.patch("saleor.plugins.webhook.shipping.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin.generate_excluded_shipping_methods_for_order_payload"
)
def test_multiple_app_with_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
    shipping_app_factory,
):
    # given
    shipping_app = shipping_app_factory()
    second_shipping_app = shipping_app_factory(app_name="shipping-app2")
    webhook_reason = "Order contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this order."

    mocked_webhook.side_effect = [
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_reason,
                }
            ]
        },
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_second_reason,
                },
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "2"),
                    "reason": webhook_second_reason,
                },
            ]
        },
    ]

    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = []

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
    assert webhook_second_reason in em.reason
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        shipping_app.webhooks.get(events__event_type=event_type),
        subscribable_object=order_with_lines,
        timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_shipping_app.webhooks.get(events__event_type=event_type),
        subscribable_object=order_with_lines,
        timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
    )
    expected_cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(order_with_lines.id)

    expected_excluded_shipping_method = [
        {"id": "1", "reason": webhook_reason},
        {"id": "1", "reason": webhook_second_reason},
        {"id": "2", "reason": webhook_second_reason},
    ]

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        (payload, expected_excluded_shipping_method),
        CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.plugins.webhook.shipping.cache.set")
@mock.patch("saleor.plugins.webhook.shipping.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin.generate_excluded_shipping_methods_for_order_payload"
)
def test_multiple_webhooks_on_the_same_app_with_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
    shipping_app_factory,
):
    # given
    shipping_app = shipping_app_factory()
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS

    # create the second webhook with the same event
    second_webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=shipping_app,
        target_url="https://shipping-gateway.com/api/",
    )
    second_webhook.events.create(
        event_type=event_type,
        webhook=second_webhook,
    )

    webhook_reason = "Order contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this order."

    mocked_webhook.side_effect = [
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_reason,
                }
            ]
        },
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_second_reason,
                },
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "2"),
                    "reason": webhook_second_reason,
                },
            ]
        },
    ]

    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = []

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
    assert webhook_second_reason in em.reason
    webhooks = shipping_app.webhooks.filter(events__event_type=event_type)
    assert len(webhooks) > 1
    for webhook in webhooks:
        mocked_webhook.assert_any_call(
            event_type,
            payload,
            webhook,
            subscribable_object=order_with_lines,
            timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
        )

    expected_cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(order_with_lines.id)

    expected_excluded_shipping_method = [
        {"id": "1", "reason": webhook_reason},
        {"id": "1", "reason": webhook_second_reason},
        {"id": "2", "reason": webhook_second_reason},
    ]

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        (payload, expected_excluded_shipping_method),
        CACHE_EXCLUDED_SHIPPING_TIME,
    )


def test_parse_excluded_shipping_methods_response(app):
    # given
    external_id = to_shipping_app_id(app, "test-1234")
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
            {
                "id": external_id,
            },
        ]
    }

    # when
    excluded_methods = get_excluded_shipping_methods_from_response(response)

    # then
    assert len(excluded_methods) == 2
    assert excluded_methods[0]["id"] == "2"
    assert excluded_methods[1]["id"] == external_id


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

    def respond(*args, **kwargs):
        return webhook_response(order_with_lines.shipping_method)

    mocked_webhook.side_effect = respond
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    # when
    response = staff_api_client.post_graphql(ORDER_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    # then
    assert len(order_data["availableShippingMethods"]) == expected_count


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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, shipping_app):
    data = '{"key": "value"}'
    webhook = shipping_app.webhooks.first()
    trigger_webhook_sync(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, data, webhook
    )
    event_delivery = EventDelivery.objects.first()
    mock_request.assert_called_once_with(shipping_app.name, event_delivery)


@mock.patch("saleor.plugins.webhook.shipping.cache.set")
@mock.patch("saleor.plugins.webhook.shipping.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin."
    "generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    shipping_app_factory,
):
    # given
    shipping_app = shipping_app_factory()
    webhook_reason = "Checkout contains dangerous products."
    other_reason = "Shipping is not applicable for this checkout."

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
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        previous_value=previous_value,
    )
    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert other_reason in em.reason
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    mocked_webhook.assert_called_once_with(
        event_type,
        payload,
        shipping_app.webhooks.get(events__event_type=event_type),
        subscribable_object=checkout_with_items,
        timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
    )

    expected_cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(checkout_with_items.token)

    expected_excluded_shipping_method = [{"id": "1", "reason": webhook_reason}]

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        (payload, expected_excluded_shipping_method),
        CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.plugins.webhook.shipping.cache.set")
@mock.patch("saleor.plugins.webhook.shipping.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin."
    "generate_excluded_shipping_methods_for_checkout_payload"
)
def test_multiple_app_with_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    shipping_app_factory,
):
    # given
    shipping_app = shipping_app_factory()
    second_shipping_app = shipping_app_factory()
    webhook_reason = "Checkout contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this checkout."

    mocked_webhook.side_effect = [
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_reason,
                }
            ]
        },
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_second_reason,
                },
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "2"),
                    "reason": webhook_second_reason,
                },
            ]
        },
    ]
    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = []

    # when
    excluded_methods = plugin.excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        previous_value=previous_value,
    )

    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert webhook_second_reason in em.reason
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        shipping_app.webhooks.get(events__event_type=event_type),
        subscribable_object=checkout_with_items,
        timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_shipping_app.webhooks.get(events__event_type=event_type),
        subscribable_object=checkout_with_items,
        timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
    )

    expected_cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(checkout_with_items.token)

    expected_excluded_shipping_method = [
        {"id": "1", "reason": webhook_reason},
        {"id": "1", "reason": webhook_second_reason},
        {"id": "2", "reason": webhook_second_reason},
    ]

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        (payload, expected_excluded_shipping_method),
        CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.plugins.webhook.shipping.cache.set")
@mock.patch("saleor.plugins.webhook.shipping.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin."
    "generate_excluded_shipping_methods_for_checkout_payload"
)
def test_multiple_webhooks_on_the_same_app_with_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    shipping_app_factory,
):
    # given
    shipping_app = shipping_app_factory()
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # create the second webhook with the same event
    second_webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=shipping_app,
        target_url="https://shipping-gateway.com/api/",
    )
    second_webhook.events.create(
        event_type=event_type,
        webhook=second_webhook,
    )

    webhook_reason = "Checkout contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this checkout."

    mocked_webhook.side_effect = [
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_reason,
                }
            ]
        },
        {
            "excluded_methods": [
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                    "reason": webhook_second_reason,
                },
                {
                    "id": graphene.Node.to_global_id("ShippingMethod", "2"),
                    "reason": webhook_second_reason,
                },
            ]
        },
    ]
    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = []

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
    assert webhook_second_reason in em.reason
    webhooks = shipping_app.webhooks.filter(events__event_type=event_type)
    assert len(webhooks) > 1
    for webhook in webhooks:
        mocked_webhook.assert_any_call(
            event_type,
            payload,
            webhook,
            subscribable_object=checkout_with_items,
            timeout=EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
        )

    expected_cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(checkout_with_items.token)

    expected_excluded_shipping_method = [
        {"id": "1", "reason": webhook_reason},
        {"id": "1", "reason": webhook_second_reason},
        {"id": "2", "reason": webhook_second_reason},
    ]

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        (payload, expected_excluded_shipping_method),
        CACHE_EXCLUDED_SHIPPING_TIME,
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
    lines, _ = fetch_checkout_lines(checkout_with_items)
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout_with_items, lines, [], manager)

    # when
    json_payload = json.loads(
        generate_excluded_shipping_methods_for_checkout_payload(
            checkout_info, available_shipping_methods=methods
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
