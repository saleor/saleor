import json
import uuid
from decimal import Decimal
from unittest import mock

import graphene
import pytest
from measurement.measures import Weight
from prices import Money

from ....shipping.interface import ShippingMethodData
from ....shipping.webhooks.shared import CACHE_EXCLUDED_SHIPPING_TIME
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ...webhooks.exclude_shipping import (
    excluded_shipping_methods_for_checkout,
)


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


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout_use_cache(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    mocked_cache_get,
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

    payload = json.dumps({"checkout": {"id": 1, "some_field": "12"}})
    mocked_payload.return_value = payload

    mocked_cache_get.return_value = (payload, [{"id": "1", "reason": webhook_reason}])

    # when
    excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=True,
        requestor=None,
    )

    # then
    assert not mocked_webhook.called

    assert not mocked_cache_set.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout_stores_in_cache_when_empty(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    mocked_cache_get,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
):
    # given
    shipping_webhook = app_exclude_shipping_for_checkout.webhooks.get()

    webhook_reason = "Order contains dangerous products."

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

    mocked_cache_get.return_value = None

    # when
    excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=True,
        requestor=None,
    )

    # then
    assert mocked_webhook.called

    expected_cache_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        app_exclude_shipping_for_checkout.id,
    )

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout_stores_in_cache_when_payload_different(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    mocked_cache_get,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
):
    # given

    shipping_webhook = app_exclude_shipping_for_checkout.webhooks.get()

    webhook_reason = "Order contains dangerous products."

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

    mocked_cache_get.return_value = None

    # when
    excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=True,
        requestor=None,
    )
    # then
    assert mocked_webhook.called

    expected_cache_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        app_exclude_shipping_for_checkout.id,
    )
    mocked_cache_get.assert_called_once_with(expected_cache_key)

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )
