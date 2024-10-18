import json
import logging
import uuid
from dataclasses import asdict
from unittest import mock

import pytest

from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....event_types import WebhookEventAsyncType
from ...utils import get_webhooks_for_event
from ..transport import (
    DeferredPayloadData,
    _generate_deferred_payload,
    create_deliveries_for_deferred_payload_events,
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
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_(
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
    call_kwargs = mocked_send_webhook_request_async.call_args.kwargs
    deferred_payload_data = call_kwargs["kwargs"]["deferred_payload_data"]

    assert deferred_payload_data["model_name"] == "checkout.checkout"
    assert deferred_payload_data["model_id"] == checkout.pk
    assert deferred_payload_data["requestor_model_name"] == "account.user"
    assert deferred_payload_data["requestor_model_id"] == staff_user.pk
    assert call_kwargs["kwargs"]["event_delivery_id"] == delivery.id

    assert delivery.event_type == event_type
    assert delivery.payload is None
    assert delivery.webhook == checkout_updated_webhook


def test_generate_deferred_payload(
    checkout_with_item, setup_checkout_webhooks, staff_user, fetch_kwargs
):
    # given
    checkout = checkout_with_item
    fetch_checkout_data(**fetch_kwargs)

    logger_obj = logging.getLogger(__name__)

    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    _, _, _, checkout_updated_webhook = setup_checkout_webhooks(event_type)
    webhooks = get_webhooks_for_event(event_type)
    payload_args = DeferredPayloadData(
        model_name="checkout.checkout",
        model_id=checkout.pk,
        requestor_model_name="account.user",
        requestor_model_id=staff_user.pk,
        request_time=None,
    )
    delivery = create_deliveries_for_deferred_payload_events(
        event_type, list(webhooks)
    )[0]

    # when
    data = _generate_deferred_payload(
        event_type=event_type,
        webhook=checkout_updated_webhook,
        payload_args=asdict(payload_args),
        delivery=delivery,
        logger_obj=logger_obj,
    )

    # then
    checkout.refresh_from_db()
    delivery.refresh_from_db()
    assert data
    assert delivery.payload
    assert delivery.payload.get_payload() == data

    data = json.loads(data)
    assert data["issuingPrincipal"]["email"] == staff_user.email
    assert (
        data["checkout"]["totalPrice"]["gross"]["amount"] == checkout.total_gross_amount
    )


def test_generate_deferred_payload_model_pk_does_not_exist(
    checkout_with_item, setup_checkout_webhooks, staff_user, fetch_kwargs
):
    # given
    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    _, _, _, checkout_updated_webhook = setup_checkout_webhooks(event_type)
    webhooks = get_webhooks_for_event(event_type)
    payload_args = DeferredPayloadData(
        model_name="checkout.checkout",
        model_id=uuid.uuid4(),
        requestor_model_name="account.user",
        requestor_model_id=999999,
        request_time=None,
    )
    delivery = create_deliveries_for_deferred_payload_events(
        event_type, list(webhooks)
    )[0]

    # when
    data = _generate_deferred_payload(
        event_type=event_type,
        webhook=checkout_updated_webhook,
        payload_args=asdict(payload_args),
        delivery=delivery,
        logger_obj=mock.Mock(),
    )

    # then
    delivery.refresh_from_db()
    assert data
    assert delivery.payload
    assert delivery.payload.get_payload() == data

    data = json.loads(data)
    assert data["issuingPrincipal"] is None
    assert data["checkout"] is None
