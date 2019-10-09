import json

import pytest

from saleor.order import OrderStatus
from saleor.webhook import WebhookEventType
from saleor.webhook.payloads import (
    generate_customer_payload,
    generate_order_payload,
    generate_product_payload,
    generate_sample_payload,
)


@pytest.mark.parametrize(
    "event_name, order_status",
    [
        (WebhookEventType.ORDER_CREATED, OrderStatus.UNFULFILLED),
        (WebhookEventType.ORDER_UPDATED, OrderStatus.CANCELED),
        (WebhookEventType.ORDER_CANCELLED, OrderStatus.CANCELED),
        (WebhookEventType.ORDER_FULFILLED, OrderStatus.UNFULFILLED),
        (WebhookEventType.ORDER_FULLY_PAID, OrderStatus.UNFULFILLED),
    ],
)
def test_generate_sample_payload_order(
    event_name, order_status, fulfilled_order, payment_txn_captured
):
    fulfilled_order.status = order_status
    fulfilled_order.save()
    payload = generate_sample_payload(event_name)
    assert payload == json.loads(generate_order_payload(fulfilled_order))


@pytest.mark.parametrize(
    "event_name",
    [
        WebhookEventType.ORDER_CREATED,
        WebhookEventType.ORDER_UPDATED,
        WebhookEventType.ORDER_CANCELLED,
        WebhookEventType.ORDER_FULFILLED,
        WebhookEventType.ORDER_FULLY_PAID,
        WebhookEventType.PRODUCT_CREATED,
        WebhookEventType.CUSTOMER_CREATED,
        "Non_existing_event",
        None,
        "",
    ],
)
def test_generate_sample_payload_empty_response_(event_name):
    assert generate_sample_payload(event_name) is None


def test_generate_sample_customer_payload(customer_user):
    payload = generate_sample_payload(WebhookEventType.CUSTOMER_CREATED)
    assert payload == json.loads(generate_customer_payload(customer_user))


def test_generate_sample_product_payload(variant):
    payload = generate_sample_payload(WebhookEventType.PRODUCT_CREATED)
    assert payload == json.loads(generate_product_payload(variant.product))
