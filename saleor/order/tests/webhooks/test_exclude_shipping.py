import json
import uuid
from decimal import Decimal
from unittest import mock
from unittest.mock import call

import graphene
import pytest
from measurement.measures import Weight
from prices import Money
from promise import Promise

from ....shipping.interface import ShippingMethodData
from ....webhook.const import CACHE_EXCLUDED_SHIPPING_TIME
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.transport.shipping_helpers import to_shipping_app_id
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ...webhooks.exclude_shipping import (
    _get_excluded_shipping_methods_from_response,
    excluded_shipping_methods_for_order,
    generate_excluded_shipping_methods_for_order_payload,
)

ORDER_QUERY_SHIPPING_METHOD = """
query OrderQuery($id: ID) {
  order(id: $id) {
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
"""


@pytest.fixture
def available_shipping_methods():
    methods = []
    for i in range(2):
        methods.append(
            ShippingMethodData(
                id=str(i),
                price=Money(Decimal(10), "usd"),
                name=uuid.uuid4().hex,
                maximum_order_weight=Weight(kg=0),
                minimum_order_weight=Weight(kg=0),
                maximum_delivery_days=0,
                minimum_delivery_days=5,
            )
        )
    return methods


@mock.patch("saleor.order.webhooks.exclude_shipping._get_excluded_shipping_data")
def test_excluded_shipping_methods_for_order_run_webhook_when_shipping_methods_provided(
    mocked_get_excluded_shipping_data, draft_order
):
    # given
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
    )

    non_empty_shipping_methods = [shipping_method]

    # when
    excluded_shipping_methods_for_order(
        order=draft_order,
        available_shipping_methods=non_empty_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    mocked_get_excluded_shipping_data.assert_called_once()


@mock.patch("saleor.order.webhooks.exclude_shipping._get_excluded_shipping_data")
def test_excluded_shipping_methods_for_order_dont_run_webhook_on_missing_shipping_methods(
    mocked_get_excluded_shipping_data, draft_order
):
    # given
    empty_shipping_methods = []

    # when
    excluded_shipping_methods_for_order(
        order=draft_order,
        available_shipping_methods=empty_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    mocked_get_excluded_shipping_data.assert_not_called()


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.trigger_webhook_sync_promise"
)
@mock.patch(
    "saleor.order.webhooks.exclude_shipping.generate_excluded_shipping_methods_for_order_payload"
)
def test_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    order_with_lines,
    available_shipping_methods,
    app_exclude_shipping_for_order,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_order
    shipping_webhook = shipping_app.webhooks.get()
    webhook_reason = "Order contains dangerous products."

    shipping_method_id_to_exclude = available_shipping_methods[0].id
    webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id(
                    "ShippingMethod", shipping_method_id_to_exclude
                ),
                "reason": webhook_reason,
            }
        ]
    }
    mocked_webhook.return_value = Promise.resolve(webhook_response)
    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    assert len(excluded_methods) == 1
    excluded_method = excluded_methods[0]
    assert excluded_method.id == shipping_method_id_to_exclude
    assert webhook_reason in excluded_method.reason

    mocked_webhook.assert_called_once_with(
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        shipping_webhook,
        False,
        static_payload=payload,
        subscribable_object=(order_with_lines, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
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
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.trigger_webhook_sync_promise"
)
@mock.patch(
    "saleor.order.webhooks.exclude_shipping.generate_excluded_shipping_methods_for_order_payload"
)
def test_multiple_app_with_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    order_with_lines,
    available_shipping_methods,
    app_exclude_shipping_for_order,
    second_app_exclude_shipping_for_order,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_order
    shipping_webhook = shipping_app.webhooks.get()

    second_shipping_app = second_app_exclude_shipping_for_order
    second_shipping_webhook = second_shipping_app.webhooks.get()
    webhook_reason = "Order contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this order."

    first_excluded_id = available_shipping_methods[0].id
    second_excluded_id = available_shipping_methods[1].id

    first_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id(
                    "ShippingMethod",
                    first_excluded_id,
                ),
                "reason": webhook_reason,
            }
        ]
    }
    second_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id(
                    "ShippingMethod",
                    first_excluded_id,
                ),
                "reason": webhook_second_reason,
            },
            {
                "id": graphene.Node.to_global_id(
                    "ShippingMethod",
                    second_excluded_id,
                ),
                "reason": webhook_second_reason,
            },
        ]
    }

    mocked_webhook.side_effect = [
        Promise.resolve(first_webhook_response),
        Promise.resolve(second_webhook_response),
    ]

    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    assert len(excluded_methods) == 2
    first_excluded_method_data = next(
        em for em in excluded_methods if em.id == first_excluded_id
    )
    assert webhook_reason in first_excluded_method_data.reason
    assert webhook_second_reason in first_excluded_method_data.reason

    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    mocked_webhook.assert_any_call(
        event_type,
        shipping_webhook,
        False,
        static_payload=payload,
        subscribable_object=(order_with_lines, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        second_shipping_webhook,
        False,
        static_payload=payload,
        subscribable_object=(order_with_lines, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
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
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.trigger_webhook_sync_promise"
)
@mock.patch(
    "saleor.order.webhooks.exclude_shipping.generate_excluded_shipping_methods_for_order_payload"
)
def test_multiple_webhooks_on_the_same_app_with_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    order_with_lines,
    available_shipping_methods,
    app_exclude_shipping_for_order,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_order
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

    mocked_webhook.side_effect = [
        Promise.resolve(first_webhook_response),
        Promise.resolve(second_webhook_response),
    ]

    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    assert len(excluded_methods) == 2
    em_1 = next(em for em in excluded_methods if em.id == "1")
    assert webhook_reason in em_1.reason
    assert webhook_second_reason in em_1.reason

    mocked_webhook.assert_any_call(
        event_type,
        first_webhook,
        False,
        static_payload=payload,
        subscribable_object=(order_with_lines, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        second_webhook,
        False,
        static_payload=payload,
        subscribable_object=(order_with_lines, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
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
    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-gateway.com/apiv2/",
    )

    # when
    excluded_methods = _get_excluded_shipping_methods_from_response(response, webhook)

    # then
    assert len(excluded_methods) == 2
    assert excluded_methods[0].id == "2"
    assert excluded_methods[1].id == external_id


def test_parse_excluded_shipping_methods_response_invalid(app):
    # given
    response = {
        "excluded_methods": [
            {
                "id": "not-an-id",
            },
        ]
    }
    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-gateway.com/apiv2/",
    )

    # when
    excluded_methods = _get_excluded_shipping_methods_from_response(response, webhook)

    # then
    assert not excluded_methods


def test_generate_excluded_shipping_methods_for_order_payload(
    order_with_lines,
    available_shipping_methods,
):
    # given
    methods = available_shipping_methods
    # when
    json_payload = json.loads(
        generate_excluded_shipping_methods_for_order_payload(
            order=order_with_lines, available_shipping_methods=methods
        )
    )
    # then
    assert len(json_payload["shipping_methods"]) == 2
    assert json_payload["shipping_methods"][0]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[0].id
    )
    assert json_payload["shipping_methods"][1]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", methods[1].id
    )
    graphql_order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    assert json_payload["order"]["id"] == graphql_order_id


@mock.patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_generate_excluded_shipping_methods_for_order(mocked_fetch, order):
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
        name="shipping",
        maximum_order_weight=Weight(kg=10),
        minimum_order_weight=Weight(g=1),
        maximum_delivery_days=10,
        minimum_delivery_days=2,
    )
    response = json.loads(
        generate_excluded_shipping_methods_for_order_payload(order, [shipping_method])
    )

    assert "order" in response
    assert response["shipping_methods"] == [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", "123"),
            "price": "10.59",
            "currency": "USD",
            "name": "shipping",
            "maximum_order_weight": "10.0:kg",
            "minimum_order_weight": "1.0:g",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]
    mocked_fetch.assert_not_called()
