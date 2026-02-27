import json
import uuid
from decimal import Decimal
from unittest import mock

import graphene
import pytest
from measurement.measures import Weight
from prices import Money
from promise import Promise

from ....graphql.core.utils import to_global_id_or_none
from ....graphql.tests.utils import get_graphql_content
from ....shipping.interface import ExcludedShippingMethod, ShippingMethodData
from ....shipping.models import ShippingMethod
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ...webhooks.exclude_shipping import (
    excluded_shipping_methods_for_checkout,
)

CHECKOUT_QUERY_SHIPPING_METHOD = """
query Checkout($id: ID){
  checkout(id: $id) {
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
"""


@pytest.fixture
def available_shipping_methods():
    return [
        ShippingMethodData(
            id="1",
            price=Money(Decimal(10), "usd"),
            name=uuid.uuid4().hex,
            maximum_order_weight=Weight(kg=0),
            minimum_order_weight=Weight(kg=0),
            maximum_delivery_days=0,
            minimum_delivery_days=5,
        ),
        ShippingMethodData(
            id="2",
            price=Money(Decimal(10), "usd"),
            name=uuid.uuid4().hex,
            maximum_order_weight=Weight(kg=0),
            minimum_order_weight=Weight(kg=0),
            maximum_delivery_days=0,
            minimum_delivery_days=5,
        ),
    ]


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
)
def test_checkout_deliveries(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
    settings,
    shipping_method_weight_based,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = (
        checkout_ready_to_complete.assigned_delivery.shipping_method_id
    )
    mocked_webhook.return_value = Promise.resolve(
        [ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)]
    )
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(checkout_ready_to_complete)},
    )
    content = get_graphql_content(response)
    checkout_data = content["data"]["checkout"]

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
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
)
def test_checkout_available_shipping_methods(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
    settings,
    shipping_method_weight_based,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"

    excluded_shipping_method_id = (
        checkout_ready_to_complete.assigned_delivery.shipping_method_id
    )
    mocked_webhook.return_value = Promise.resolve(
        [ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)]
    )

    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(checkout_ready_to_complete)},
    )
    content = get_graphql_content(response)
    shipping_methods = content["data"]["checkout"]["availableShippingMethods"]
    # then
    assert len(shipping_methods) == 1
    assert shipping_methods[0]["active"]


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
)
def test_checkout_deliveries_webhook_called_once(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
):
    # given
    mocked_webhook.side_effect = [Promise.resolve([]), AssertionError("called twice.")]
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)

    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(checkout_ready_to_complete)},
    )
    content = get_graphql_content(response)
    checkout_data = content["data"]["checkout"]

    # then
    expected_count = ShippingMethod.objects.count()
    assert len(checkout_data["availableShippingMethods"]) == expected_count
    assert len(checkout_data["shippingMethods"]) == expected_count
    assert mocked_webhook.called


@mock.patch("saleor.shipping.webhooks.shared.trigger_webhook_sync_promise")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout_webhook_with_subscription(
    mocked_static_payload,
    mocked_webhook,
    checkout_with_items,
    available_shipping_methods,
    exclude_shipping_app_with_subscription,
    settings,
):
    # given
    shipping_app = exclude_shipping_app_with_subscription
    shipping_webhook = shipping_app.webhooks.get()
    webhook_reason = "Checkout contains dangerous products."

    webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    mocked_webhook.return_value = Promise.resolve(webhook_response)

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_static_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()
    # then
    assert len(excluded_methods) == 1
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason

    mocked_webhook.assert_called_once_with(
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        webhook=shipping_webhook,
        allow_replica=False,
        static_payload=payload,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        requestor=None,
    )


@mock.patch("saleor.shipping.webhooks.shared.trigger_webhook_sync_promise")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_multiple_app_with_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
    second_app_exclude_shipping_for_checkout,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_checkout
    shipping_webhook = shipping_app.webhooks.get()

    second_shipping_app = second_app_exclude_shipping_for_checkout
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

    mocked_webhook.side_effect = [
        Promise.resolve(first_webhook_response),
        Promise.resolve(second_webhook_response),
    ]

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert webhook_second_reason in em.reason
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    mocked_webhook.assert_any_call(
        event_type=event_type,
        webhook=shipping_webhook,
        allow_replica=False,
        static_payload=payload,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        requestor=None,
    )
    mocked_webhook.assert_any_call(
        event_type=event_type,
        webhook=second_shipping_webhook,
        allow_replica=False,
        static_payload=payload,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        requestor=None,
    )
    assert mocked_webhook.call_count == 2


@mock.patch("saleor.shipping.webhooks.shared.trigger_webhook_sync_promise")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_multiple_webhooks_on_the_same_app_with_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_checkout
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

    mocked_webhook.side_effect = [
        Promise.resolve(first_webhook_response),
        Promise.resolve(second_webhook_response),
    ]

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout=checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert webhook_second_reason in em.reason

    mocked_webhook.assert_any_call(
        event_type=event_type,
        webhook=first_webhook,
        allow_replica=False,
        static_payload=payload,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        requestor=None,
    )
    mocked_webhook.assert_any_call(
        event_type=event_type,
        webhook=second_webhook,
        allow_replica=False,
        static_payload=payload,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        requestor=None,
    )
    assert mocked_webhook.call_count == 2


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_excluded_shipping_methods_for_checkout(
    mocked_webhook,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
):
    # given
    webhook_reason = "Order contains dangerous products."

    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    assert len(excluded_methods) == 1
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    mocked_webhook.assert_called_once()
