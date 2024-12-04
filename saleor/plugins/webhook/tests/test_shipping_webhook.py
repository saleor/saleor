import json
from unittest import mock
from unittest.mock import call

import graphene
import pytest

from ....core.models import EventDelivery
from ....graphql.tests.utils import get_graphql_content
from ....graphql.webhook.utils import get_subscription_query_hash
from ....order import OrderStatus
from ....webhook.const import CACHE_EXCLUDED_SHIPPING_TIME
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.payloads import (
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
)
from ....webhook.transport.shipping import (
    get_excluded_shipping_methods_from_response,
    get_excluded_shipping_methods_or_fetch,
    parse_list_shipping_methods_response,
    to_shipping_app_id,
)
from ....webhook.transport.synchronous.transport import trigger_webhook_sync
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ...base_plugin import ExcludedShippingMethod

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


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
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
    settings,
):
    # given
    shipping_app = shipping_app_factory()
    shipping_webhook = shipping_app.webhooks.get()
    webhook_reason = "Order contains dangerous products."
    other_reason = "Shipping is not applicable for this order."
    webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    mocked_webhook.return_value = webhook_response
    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
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
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        payload,
        shipping_webhook,
        False,
        subscribable_object=order_with_lines,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    expected_cache_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
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
    settings,
):
    # given
    shipping_app = shipping_app_factory()
    shipping_webhook = shipping_app.webhooks.get()

    second_shipping_app = shipping_app_factory(app_name="shipping-app2")
    second_shipping_webhook = second_shipping_app.webhooks.get()
    webhook_reason = "Order contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this order."
    first_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    second_webhook_response = {
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
    }

    mocked_webhook.side_effect = [first_webhook_response, second_webhook_response]

    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
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
        shipping_webhook,
        False,
        subscribable_object=order_with_lines,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_shipping_webhook,
        False,
        subscribable_object=order_with_lines,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    assert mocked_webhook.call_count == 2
    expected_cache_for_first_webhook_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )
    expected_cache_for_second_webhook_key = generate_cache_key_for_webhook(
        payload_dict,
        second_shipping_webhook.target_url,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        second_shipping_app.id,
    )

    assert expected_cache_for_first_webhook_key != expected_cache_for_second_webhook_key

    mocked_cache_set.assert_has_calls(
        [
            call(
                expected_cache_for_first_webhook_key,
                first_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
            call(
                expected_cache_for_second_webhook_key,
                second_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
        ]
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
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
    settings,
):
    # given
    shipping_app = shipping_app_factory()
    first_webhook = shipping_app.webhooks.get()
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS

    # create the second webhook with the same event
    second_webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=shipping_app,
        target_url="https://shipping-gateway.com/apiv2/",
    )
    second_webhook.events.create(
        event_type=event_type,
        webhook=second_webhook,
    )

    webhook_reason = "Order contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this order."

    first_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    second_webhook_response = {
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
    }

    mocked_webhook.side_effect = [first_webhook_response, second_webhook_response]

    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
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

    mocked_webhook.assert_any_call(
        event_type,
        payload,
        first_webhook,
        False,
        subscribable_object=order_with_lines,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_webhook,
        False,
        subscribable_object=order_with_lines,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    assert mocked_webhook.call_count == 2

    expected_cache_for_first_webhook_key = generate_cache_key_for_webhook(
        payload_dict,
        first_webhook.target_url,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )
    expected_cache_for_second_webhook_key = generate_cache_key_for_webhook(
        payload_dict,
        second_webhook.target_url,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )
    assert expected_cache_for_first_webhook_key != expected_cache_for_second_webhook_key

    mocked_cache_set.assert_has_calls(
        [
            call(
                expected_cache_for_first_webhook_key,
                first_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
            call(
                expected_cache_for_second_webhook_key,
                second_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
        ]
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
    permission_group_manage_orders,
    settings,
):
    # given
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.save(update_fields=["status"])
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = order_with_lines.shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)
    ]
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    # when
    response = staff_api_client.post_graphql(ORDER_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    shipping_methods = order_data["shippingMethods"]
    # then
    assert len(shipping_methods) == 1
    assert not shipping_methods[0]["active"]
    assert shipping_methods[0]["message"] == webhook_reason


@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_order"
)
def test_draft_order_shipping_methods(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    settings,
):
    # given
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.save(update_fields=["status"])
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = order_with_lines.shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)
    ]
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = """
      query DraftOrdersQuery {
       draftOrders(first: 1) {
         edges {
           node {
             shippingMethods {
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
    # when
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content["data"]["draftOrders"]["edges"][0]["node"]

    shipping_methods = order_data["shippingMethods"]
    # then
    assert len(shipping_methods) == 1
    assert not shipping_methods[0]["active"]
    assert shipping_methods[0]["message"] == webhook_reason


@pytest.mark.parametrize(
    "order_status",
    [
        OrderStatus.UNFULFILLED,
        OrderStatus.PARTIALLY_FULFILLED,
        OrderStatus.FULFILLED,
        OrderStatus.CANCELED,
        OrderStatus.EXPIRED,
        OrderStatus.RETURNED,
        OrderStatus.PARTIALLY_RETURNED,
    ],
)
@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_order"
)
def test_order_shipping_methods_skips_sync_webhook_for_non_editable_statuses(
    mocked_webhook,
    order_status,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    settings,
):
    # given
    order_with_lines.status = order_status
    order_with_lines.save(update_fields=["status"])
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_QUERY_SHIPPING_METHOD)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    shipping_methods = order_data["shippingMethods"]

    # then
    assert not mocked_webhook.called
    assert len(shipping_methods) == 1
    assert shipping_methods[0]["active"]


@pytest.mark.parametrize(
    ("webhook_response", "expected_count"),
    [(lambda s: [ExcludedShippingMethod(s.id, "")], 0), (lambda s: [], 1)],
)
@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_order"
)
def test_order_available_shipping_methods(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    settings,
    webhook_response,
    expected_count,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.save(update_fields=["status"])
    shipping_method = order_with_lines.shipping_method

    def respond(*args, **kwargs):
        return webhook_response(shipping_method)

    mocked_webhook.side_effect = respond
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, shipping_app):
    data = '{"key": "value"}'
    webhook = shipping_app.webhooks.first()
    trigger_webhook_sync(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, data, webhook, False
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin."
    "generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout_webhook_without_pregenerated_payload(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    shipping_app_factory,
    settings,
):
    # given
    shipping_app = shipping_app_factory()
    shipping_webhook = shipping_app.webhooks.get()
    webhook_reason = "Checkout contains dangerous products."
    other_reason = "Shipping is not applicable for this checkout."

    webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    mocked_webhook.return_value = webhook_response

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
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

    mocked_webhook.assert_called_once_with(
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        payload,
        shipping_webhook,
        False,
        subscribable_object=checkout_with_items,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    expected_cache_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin."
    "generate_excluded_shipping_methods_for_checkout_payload"
)
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_excluded_shipping_methods_for_checkout_webhook_with_subscription_base_pregenerated_payload(
    mocked_subscription_payload,
    mocked_static_payload,
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    exclude_shipping_app_with_subscription,
    settings,
):
    # given
    shipping_app = exclude_shipping_app_with_subscription
    shipping_webhook = shipping_app.webhooks.get()
    webhook_reason = "Checkout contains dangerous products."
    other_reason = "Shipping is not applicable for this checkout."

    webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    mocked_webhook.return_value = webhook_response

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    query_hash = get_subscription_query_hash(shipping_webhook.subscription_query)
    pregenerated_payloads = {shipping_app.id: {query_hash: payload_dict}}
    payload = json.dumps(payload_dict)
    mocked_static_payload.return_value = payload

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
        pregenerated_subscription_payloads=pregenerated_payloads,
    )
    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert other_reason in em.reason

    mocked_webhook.assert_called_once_with(
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        payload,
        shipping_webhook,
        False,
        subscribable_object=checkout_with_items,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=payload_dict,
    )
    expected_cache_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )
    mocked_subscription_payload.assert_not_called()


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_excluded_shipping_methods_for_checkout(
    mocked_webhook,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    shipping_app_factory,
):
    # given
    shipping_app_factory()
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
    mocked_webhook.assert_called_once()


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
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
    settings,
):
    # given
    shipping_app = shipping_app_factory()
    shipping_webhook = shipping_app.webhooks.get()

    second_shipping_app = shipping_app_factory()
    second_shipping_webhook = second_shipping_app.webhooks.get()

    webhook_reason = "Checkout contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this checkout."

    first_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    second_webhook_response = {
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
    }

    mocked_webhook.side_effect = [first_webhook_response, second_webhook_response]

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
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
        shipping_webhook,
        False,
        subscribable_object=checkout_with_items,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_shipping_webhook,
        False,
        subscribable_object=checkout_with_items,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    assert mocked_webhook.call_count == 2

    expected_cache_for_first_webhook_key = generate_cache_key_for_webhook(
        payload_dict, shipping_webhook.target_url, event_type, shipping_app.id
    )
    expected_cache_for_second_webhook_key = generate_cache_key_for_webhook(
        payload_dict,
        second_shipping_webhook.target_url,
        event_type,
        second_shipping_app.id,
    )

    assert expected_cache_for_first_webhook_key != expected_cache_for_second_webhook_key

    mocked_cache_set.assert_has_calls(
        [
            call(
                expected_cache_for_first_webhook_key,
                first_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
            call(
                expected_cache_for_second_webhook_key,
                second_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
        ]
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
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
    settings,
):
    # given
    shipping_app = shipping_app_factory()
    first_webhook = shipping_app.webhooks.get()
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # create the second webhook with the same event
    second_webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=shipping_app,
        target_url="https://shipping-gateway.com/apiv2/",
    )
    second_webhook.events.create(
        event_type=event_type,
        webhook=second_webhook,
    )

    webhook_reason = "Checkout contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this checkout."

    first_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    second_webhook_response = {
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
    }

    mocked_webhook.side_effect = [first_webhook_response, second_webhook_response]

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
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

    mocked_webhook.assert_any_call(
        event_type,
        payload,
        first_webhook,
        False,
        subscribable_object=checkout_with_items,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_webhook,
        False,
        subscribable_object=checkout_with_items,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    assert mocked_webhook.call_count == 2

    expected_cache_for_first_webhook_key = generate_cache_key_for_webhook(
        payload_dict, first_webhook.target_url, event_type, shipping_app.id
    )
    expected_cache_for_second_webhook_key = generate_cache_key_for_webhook(
        payload_dict, second_webhook.target_url, event_type, shipping_app.id
    )
    assert expected_cache_for_first_webhook_key != expected_cache_for_second_webhook_key

    mocked_cache_set.assert_has_calls(
        [
            call(
                expected_cache_for_first_webhook_key,
                first_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
            call(
                expected_cache_for_second_webhook_key,
                second_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
        ]
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
            checkout_with_items, available_shipping_methods=methods
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


@mock.patch("saleor.webhook.transport.shipping.parse_excluded_shipping_methods")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.webhook.transport.shipping.get_excluded_shipping_methods_from_response"
)
def test_get_excluded_shipping_methods_or_fetch_invalid_response_type(
    mocked_get_excluded,
    mocked_webhook_sync_trigger,
    mocked_parse,
    app,
    checkout,
):
    # given
    mocked_webhook_sync_trigger.return_value = ["incorrect_type"]
    webhook = Webhook.objects.create(
        name="Simple webhook", app=app, target_url="http://www.example.com/test"
    )
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    webhook.events.create(event_type=event_type)
    webhooks = Webhook.objects.all()

    # when
    get_excluded_shipping_methods_or_fetch(
        webhooks, event_type, '{"test":"payload"}', checkout, False, None
    )
    # then
    mocked_get_excluded.asssert_not_called()
    mocked_parse.assert_called_once_with([])


def test_parse_list_shipping_methods_response_response_incorrect_format(app):
    # given
    response_data_with_incorrect_format = [[1], 2, "3"]
    # when
    result = parse_list_shipping_methods_response(
        response_data_with_incorrect_format, app
    )
    # then
    assert result == []


def test_parse_list_shipping_methods_with_metadata(app):
    # given
    response_data_with_meta = [
        {
            "id": 123,
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
            "metadata": {"field": "value"},
        }
    ]
    # when
    response = parse_list_shipping_methods_response(response_data_with_meta, app)
    # then
    assert response[0].metadata == response_data_with_meta[0]["metadata"]
    assert response[0].description == response_data_with_meta[0]["description"]


def test_parse_list_shipping_methods_with_metadata_in_incorrect_format(app):
    # given
    response_data_with_meta = [
        {
            "id": 123,
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
            "metadata": {"field": None},
        }
    ]
    # when
    response = parse_list_shipping_methods_response(response_data_with_meta, app)
    # then
    assert response[0].metadata == {}


def test_parse_list_shipping_methods_metadata_absent_in_response(app):
    # given
    response_data_with_meta = [
        {
            "id": 123,
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]
    # when
    response = parse_list_shipping_methods_response(response_data_with_meta, app)
    # then
    assert response[0].metadata == {}


def test_parse_list_shipping_methods_metadata_is_none(app):
    # given
    response_data_with_meta = [
        {
            "id": 123,
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
            "metadata": None,
        }
    ]
    # when
    response = parse_list_shipping_methods_response(response_data_with_meta, app)
    # then
    assert response[0].metadata == {}
