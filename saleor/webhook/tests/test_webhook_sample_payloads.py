import copy
import json
from unittest import mock

import freezegun
import graphene
import pytest
from freezegun import freeze_time

from ...order import OrderStatus
from ..event_types import WebhookEventAsyncType
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


@freezegun.freeze_time("1914-06-28 10:50", ignore=["faker"])
@pytest.mark.parametrize(
    "event_name, order_status",
    [
        (WebhookEventAsyncType.ORDER_CREATED, OrderStatus.UNFULFILLED),
        (WebhookEventAsyncType.ORDER_UPDATED, OrderStatus.CANCELED),
        (WebhookEventAsyncType.ORDER_CANCELLED, OrderStatus.CANCELED),
        (WebhookEventAsyncType.ORDER_FULFILLED, OrderStatus.FULFILLED),
        (WebhookEventAsyncType.ORDER_FULLY_PAID, OrderStatus.FULFILLED),
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
    order_payload = json.loads(generate_order_payload(order))
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


@freeze_time("1914-06-28 10:50", ignore=["faker"])
def test_generate_sample_payload_fulfillment_created(fulfillment):
    sample_fulfillment_payload = generate_sample_payload(
        WebhookEventAsyncType.FULFILLMENT_CREATED
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
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_FULFILLED,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
        WebhookEventAsyncType.DRAFT_ORDER_DELETED,
        WebhookEventAsyncType.PRODUCT_CREATED,
        WebhookEventAsyncType.PRODUCT_UPDATED,
        "Non_existing_event",
        None,
        "",
    ],
)
def test_generate_sample_payload_empty_response_(event_name):
    assert generate_sample_payload(event_name) is None


def test_generate_sample_customer_payload(customer_user):
    payload = generate_sample_payload(WebhookEventAsyncType.CUSTOMER_CREATED)
    assert payload
    # Assert that the payload was generated from the fake user
    assert payload[0]["email"] != customer_user.email


@freeze_time("1914-06-28 10:50")
def test_generate_sample_product_payload(variant):
    payload = generate_sample_payload(WebhookEventAsyncType.PRODUCT_CREATED)
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


@freeze_time("1914-06-28 10:50", ignore=["faker"])
@pytest.mark.parametrize(
    "user_checkouts", ["regular", "click_and_collect"], indirect=True
)
def test_generate_sample_checkout_payload(user_checkouts):

    with mock.patch(
        "saleor.webhook.payloads._get_sample_object", return_value=user_checkouts
    ):
        checkout = user_checkouts
        payload = generate_sample_payload(WebhookEventAsyncType.CHECKOUT_UPDATED)
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
