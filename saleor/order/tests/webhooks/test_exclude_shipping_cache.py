import json
import uuid
from decimal import Decimal
from unittest import mock

import graphene
import pytest
from measurement.measures import Weight
from prices import Money

from ....core.prices import quantize_price
from ....shipping.interface import ShippingMethodData
from ....shipping.webhooks.shared import CACHE_EXCLUDED_SHIPPING_TIME
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ...webhooks.exclude_shipping import (
    excluded_shipping_methods_for_order,
)


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


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.order.webhooks.exclude_shipping.generate_excluded_shipping_methods_for_order_payload"
)
def test_excluded_shipping_methods_for_order_use_cache(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    mocked_cache_get,
    order_with_lines,
    available_shipping_methods,
    app_exclude_shipping_for_order,
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
    payload = json.dumps({"order": {"id": 1, "some_field": "12"}})
    mocked_payload.return_value = payload

    mocked_cache_get.return_value = (payload, [{"id": "1", "reason": webhook_reason}])

    # when
    excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    )

    # then
    assert not mocked_webhook.called

    assert not mocked_cache_set.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.order.webhooks.exclude_shipping.generate_excluded_shipping_methods_for_order_payload"
)
def test_excluded_shipping_methods_for_order_stores_in_cache_when_empty(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    mocked_cache_get,
    order_with_lines,
    available_shipping_methods,
    app_exclude_shipping_for_order,
):
    # given
    shipping_app = app_exclude_shipping_for_order
    shipping_webhook = shipping_app.webhooks.get()
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

    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload
    expected_cache_key_data = {
        "order": {
            "id": 1,
            "some_field": "12",
            "base_shipping_price_amount": str(
                quantize_price(
                    order_with_lines.base_shipping_price.amount,
                    order_with_lines.currency,
                )
            ),
            "lines_pricing": [
                {
                    "base_unit_price_amount": str(
                        quantize_price(
                            line.base_unit_price.amount, order_with_lines.currency
                        )
                    ),
                }
                for line in order_with_lines.lines.all()
            ],
        }
    }

    mocked_cache_get.return_value = None

    # when
    excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    )

    # then
    assert mocked_webhook.called

    expected_cache_key = generate_cache_key_for_webhook(
        expected_cache_key_data,
        shipping_webhook.target_url,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        shipping_app.id,
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
    "saleor.order.webhooks.exclude_shipping.generate_excluded_shipping_methods_for_order_payload"
)
def test_excluded_shipping_methods_for_order_stores_in_cache_when_payload_is_different(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    mocked_cache_get,
    order_with_lines,
    available_shipping_methods,
    app_exclude_shipping_for_order,
):
    # given
    shipping_app = app_exclude_shipping_for_order
    shipping_webhook = shipping_app.webhooks.get()
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

    payload_dict = {"order": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload
    expected_cache_key_data = {
        "order": {
            "id": 1,
            "some_field": "12",
            "base_shipping_price_amount": str(
                quantize_price(
                    order_with_lines.base_shipping_price.amount,
                    order_with_lines.currency,
                )
            ),
            "lines_pricing": [
                {
                    "base_unit_price_amount": str(
                        quantize_price(
                            line.base_unit_price.amount, order_with_lines.currency
                        )
                    ),
                }
                for line in order_with_lines.lines.all()
            ],
        }
    }

    mocked_cache_get.return_value = None

    # when
    excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    )
    # then
    assert mocked_webhook.called

    expected_cache_key = generate_cache_key_for_webhook(
        expected_cache_key_data,
        shipping_webhook.target_url,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )

    mocked_cache_get.assert_called_once_with(expected_cache_key)
    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )
