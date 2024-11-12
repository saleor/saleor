import json
import uuid
from dataclasses import asdict
from unittest import mock

import pytest

from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....core import EventDeliveryStatus
from .....core.models import EventDelivery
from ....event_types import WebhookEventAsyncType
from ...utils import get_webhooks_for_event
from ..transport import (
    DeferredPayloadData,
    generate_deferred_payloads,
    trigger_webhooks_async,
)


@pytest.fixture
def fetch_kwargs(checkout_with_items, plugins_manager):
    lines, _ = fetch_checkout_lines(checkout_with_items)
    return {
        "checkout_info": fetch_checkout_info(
            checkout_with_items, lines, plugins_manager
        ),
        "manager": plugins_manager,
        "lines": lines,
        "address": checkout_with_items.shipping_address
        or checkout_with_items.billing_address,
    }


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
def test_call_trigger_webhook_async_deferred_payload(
    mocked_generate_deferred_payloads,
    checkout_with_item,
    setup_checkout_webhooks,
    staff_user,
):
    # given
    checkout = checkout_with_item
    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    _, _, _, checkout_updated_webhook = setup_checkout_webhooks(event_type)
    webhooks = get_webhooks_for_event(event_type)

    # when
    trigger_webhooks_async(
        data=None,
        event_type=event_type,
        webhooks=webhooks,
        subscribable_object=checkout,
        requestor=staff_user,
    )

    # then
    delivery = checkout_updated_webhook.eventdelivery_set.first()
    call_kwargs = mocked_generate_deferred_payloads.call_args.kwargs
    deferred_payload_data = call_kwargs["kwargs"]["deferred_payload_data"]

    assert deferred_payload_data["model_name"] == "checkout.checkout"
    assert deferred_payload_data["object_id"] == checkout.pk
    assert deferred_payload_data["requestor_model_name"] == "account.user"
    assert deferred_payload_data["requestor_object_id"] == staff_user.pk
    assert call_kwargs["kwargs"]["event_delivery_ids"] == [delivery.id]

    assert delivery.event_type == event_type
    assert delivery.payload is None
    assert delivery.webhook == checkout_updated_webhook


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_generate_deferred_payload(
    mocked_send_webhook_request_async,
    checkout_with_item,
    setup_checkout_webhooks,
    staff_user,
    fetch_kwargs,
):
    # given
    checkout = checkout_with_item
    fetch_checkout_data(**fetch_kwargs)

    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    _, _, _, checkout_updated_webhook = setup_checkout_webhooks(event_type)
    deferred_payload_data = DeferredPayloadData(
        model_name="checkout.checkout",
        object_id=checkout.pk,
        requestor_model_name="account.user",
        requestor_object_id=staff_user.pk,
        request_time=None,
    )
    delivery = EventDelivery(
        event_type=event_type,
        webhook=checkout_updated_webhook,
        status=EventDeliveryStatus.PENDING,
    )
    delivery.save()

    # when
    generate_deferred_payloads.delay(
        event_delivery_ids=[delivery.pk],
        deferred_payload_data=asdict(deferred_payload_data),
    )

    # then
    checkout.refresh_from_db()
    delivery.refresh_from_db()
    assert delivery.payload

    data = delivery.payload.get_payload()
    data = json.loads(data)

    assert data["issuingPrincipal"]["email"] == staff_user.email
    assert (
        data["checkout"]["totalPrice"]["gross"]["amount"] == checkout.total_gross_amount
    )

    assert mocked_send_webhook_request_async.call_count == 1
    call_kwargs = mocked_send_webhook_request_async.call_args.kwargs
    assert call_kwargs["kwargs"]["event_delivery_id"] == delivery.pk


def test_generate_deferred_payload_model_pk_does_not_exist(
    checkout_with_item, setup_checkout_webhooks, staff_user, fetch_kwargs
):
    # given
    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    _, _, _, checkout_updated_webhook = setup_checkout_webhooks(event_type)
    deferred_payload_data = DeferredPayloadData(
        model_name="checkout.checkout",
        object_id=uuid.uuid4(),
        requestor_model_name="account.user",
        requestor_object_id=999999,
        request_time=None,
    )
    delivery = EventDelivery(
        event_type=event_type,
        webhook=checkout_updated_webhook,
        status=EventDeliveryStatus.PENDING,
    )
    delivery.save()

    # when
    generate_deferred_payloads.delay(
        event_delivery_ids=[delivery.pk],
        deferred_payload_data=asdict(deferred_payload_data),
    )

    # then
    delivery.refresh_from_db()
    assert delivery.status == EventDeliveryStatus.FAILED
    assert delivery.payload is None


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async",
    wraps=generate_deferred_payloads.apply_async,
)
def test_pass_queue_to_send_webhook_request_async(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    checkout_with_item,
    setup_checkout_webhooks,
    staff_user,
):
    # given
    checkout = checkout_with_item
    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    _, _, _, checkout_updated_webhook = setup_checkout_webhooks(event_type)
    webhooks = get_webhooks_for_event(event_type)
    queue = "checkout_queue"

    # when
    trigger_webhooks_async(
        data=None,
        event_type=event_type,
        webhooks=webhooks,
        subscribable_object=checkout,
        requestor=staff_user,
        queue=queue,
    )

    # then
    call_kwargs_generate_payloads = mocked_generate_deferred_payloads.call_args.kwargs
    assert "queue" not in call_kwargs_generate_payloads
    assert call_kwargs_generate_payloads["kwargs"]["send_webhook_queue"] == queue

    call_kwargs_send_webhook_request = (
        mocked_send_webhook_request_async.call_args.kwargs
    )
    assert call_kwargs_send_webhook_request["queue"] == queue
