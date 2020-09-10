import copy
import json

import graphene
import pytest

from ...order import OrderStatus
from ..event_types import WebhookEventType
from ..payloads import (
    generate_checkout_payload,
    generate_fulfillment_payload,
    generate_order_payload,
    generate_product_payload,
    generate_sample_payload,
)


def _remove_anonymized_order_data(order_data: dict) -> dict:
    order_data = copy.deepcopy(order_data)
    del order_data["id"]
    del order_data["user_email"]
    del order_data["billing_address"]
    del order_data["shipping_address"]
    del order_data["metadata"]
    del order_data["private_metadata"]
    return order_data


@pytest.mark.parametrize(
    "event_name, order_status",
    [
        (WebhookEventType.ORDER_CREATED, OrderStatus.UNFULFILLED),
        (WebhookEventType.ORDER_UPDATED, OrderStatus.CANCELED),
        (WebhookEventType.ORDER_CANCELLED, OrderStatus.CANCELED),
        (WebhookEventType.ORDER_FULFILLED, OrderStatus.FULFILLED),
        (WebhookEventType.ORDER_FULLY_PAID, OrderStatus.FULFILLED),
    ],
)
def test_generate_sample_payload_order(
    event_name, order_status, fulfilled_order, payment_txn_captured
):
    order = fulfilled_order
    order.status = order_status
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)

    payload = generate_sample_payload(event_name)
    order_payload = json.loads(generate_order_payload(fulfilled_order))
    # Check anonymized data differ
    assert order_id == payload[0]["id"]
    assert order.user_email != payload[0]["user_email"]
    assert (
        order.billing_address.street_address_1
        != payload[0]["billing_address"]["street_address_1"]
    )
    assert (
        order.shipping_address.street_address_1
        != payload[0]["shipping_address"]["street_address_1"]
    )
    assert order.metadata != payload[0]["metadata"]
    assert order.private_metadata != payload[0]["private_metadata"]
    # Remove anonymized data
    payload = _remove_anonymized_order_data(payload[0])
    order_payload = _remove_anonymized_order_data(order_payload[0])
    # Compare the payloads
    assert payload == order_payload


def test_generate_sample_payload_fulfillment_created(fulfillment):
    sample_fulfillment_payload = generate_sample_payload(
        WebhookEventType.FULFILLMENT_CREATED
    )[0]
    fulfillment_payload = json.loads(generate_fulfillment_payload(fulfillment))[0]
    order = fulfillment.order

    obj_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    order_id = graphene.Node.to_global_id("Order", order.id)

    assert obj_id == sample_fulfillment_payload["id"]
    # Check anonymized data differ
    assert order_id == sample_fulfillment_payload["order"]["id"]
    assert order.user_email != sample_fulfillment_payload["order"]["user_email"]
    assert (
        order.shipping_address.street_address_1
        != sample_fulfillment_payload["order"]["shipping_address"]["street_address_1"]
    )
    assert order.metadata != sample_fulfillment_payload["order"]["metadata"]
    assert (
        order.private_metadata
        != sample_fulfillment_payload["order"]["private_metadata"]
    )

    # Remove anonymized data
    sample_fulfillment_payload["order"] = _remove_anonymized_order_data(
        sample_fulfillment_payload["order"]
    )
    fulfillment_payload["order"] = _remove_anonymized_order_data(
        fulfillment_payload["order"]
    )
    # Compare the payloads
    assert sample_fulfillment_payload == fulfillment_payload


@pytest.mark.parametrize(
    "event_name",
    [
        WebhookEventType.ORDER_CREATED,
        WebhookEventType.ORDER_UPDATED,
        WebhookEventType.ORDER_CANCELLED,
        WebhookEventType.ORDER_FULFILLED,
        WebhookEventType.ORDER_FULLY_PAID,
        WebhookEventType.PRODUCT_CREATED,
        WebhookEventType.PRODUCT_UPDATED,
        "Non_existing_event",
        None,
        "",
    ],
)
def test_generate_sample_payload_empty_response_(event_name):
    assert generate_sample_payload(event_name) is None


def test_generate_sample_customer_payload(customer_user):
    payload = generate_sample_payload(WebhookEventType.CUSTOMER_CREATED)
    assert payload
    # Assert that the payload was generated from the fake user
    assert payload[0]["email"] != customer_user.email


def test_generate_sample_product_payload(variant):
    payload = generate_sample_payload(WebhookEventType.PRODUCT_CREATED)
    product = variant.product
    product.refresh_from_db()
    assert payload == json.loads(generate_product_payload(variant.product))


def _remove_anonymized_checkout_data(checkout_data: dict) -> dict:
    checkout_data = copy.deepcopy(checkout_data)
    del checkout_data[0]["token"]
    del checkout_data[0]["user"]
    del checkout_data[0]["email"]
    del checkout_data[0]["billing_address"]
    del checkout_data[0]["shipping_address"]
    del checkout_data[0]["metadata"]
    del checkout_data[0]["private_metadata"]
    return checkout_data


def test_generate_sample_checkout_payload(user_checkout_with_items):
    checkout = user_checkout_with_items
    payload = generate_sample_payload(WebhookEventType.CHECKOUT_QUANTITY_CHANGED)
    checkout_payload = json.loads(generate_checkout_payload(checkout))
    # Check anonymized data differ
    assert checkout.token != payload[0]["token"]
    assert checkout.user.email != payload[0]["user"]["email"]
    assert checkout.email != payload[0]["email"]
    assert (
        checkout.billing_address.street_address_1
        != payload[0]["billing_address"]["street_address_1"]
    )
    assert (
        checkout.shipping_address.street_address_1
        != payload[0]["shipping_address"]["street_address_1"]
    )
    assert "note" not in payload[0]
    assert checkout.metadata != payload[0]["metadata"]
    assert checkout.private_metadata != payload[0]["private_metadata"]
    # Remove anonymized data
    payload = _remove_anonymized_checkout_data(payload)
    checkout_payload = _remove_anonymized_checkout_data(checkout_payload)
    # Compare the payloads
    assert payload == checkout_payload
