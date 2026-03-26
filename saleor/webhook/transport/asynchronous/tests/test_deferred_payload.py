import datetime
import json
import uuid
from dataclasses import asdict
from decimal import Decimal
from unittest import mock

import graphene
import pytest

from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....core import EventDeliveryStatus
from .....core.models import EventDelivery
from .....product.interface import VariantDiscountedPriceChange
from ....event_types import WebhookEventAsyncType
from ....tests.subscription_webhooks.subscription_queries import (
    PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED,
)
from ....utils import get_webhooks_for_event
from ..transport import (
    DeferredPayloadData,
    _reconstruct_subscribable_object,
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
    deferred_request_time = datetime.datetime(2020, 10, 5, tzinfo=datetime.UTC)

    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    _, _, _, checkout_updated_webhook = setup_checkout_webhooks(event_type)
    deferred_payload_data = DeferredPayloadData(
        model_name="checkout.checkout",
        object_id=checkout.pk,
        requestor_model_name="account.user",
        requestor_object_id=staff_user.pk,
        request_time=deferred_request_time,
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
    assert data["issuedAt"] == deferred_request_time.isoformat()
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


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport"
    ".generate_deferred_payloads.apply_async"
)
def test_call_trigger_webhook_async_deferred_payload_with_dataclass(
    mocked_generate_deferred_payloads,
    variant_with_many_stocks,
    channel_USD,
    subscription_webhook,
    staff_user,
):
    # given
    variant = variant_with_many_stocks
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED

    webhook = subscription_webhook(PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED, event_type)
    webhooks = get_webhooks_for_event(event_type)

    previous_price = Decimal("10.00")
    new_price = Decimal("8.00")
    currency = channel_USD.currency_code

    price_info = VariantDiscountedPriceChange(
        variant_id=variant.id,
        channel_id=channel_USD.id,
        channel_slug=channel_USD.slug,
        previous_price_amount=previous_price,
        new_price_amount=new_price,
        currency=currency,
    )

    # when
    trigger_webhooks_async(
        data=None,
        event_type=event_type,
        webhooks=webhooks,
        subscribable_object=price_info,
        requestor=staff_user,
    )

    # then
    delivery = webhook.eventdelivery_set.first()
    call_kwargs = mocked_generate_deferred_payloads.call_args.kwargs
    deferred_payload_data = call_kwargs["kwargs"]["deferred_payload_data"]

    assert deferred_payload_data["model_name"] is None
    assert deferred_payload_data["object_id"] is None
    assert deferred_payload_data["subscribable_object_data"] == {
        "variant_id": variant.id,
        "channel_id": channel_USD.id,
        "channel_slug": channel_USD.slug,
        "previous_price_amount": str(previous_price),
        "new_price_amount": str(new_price),
        "currency": currency,
    }
    assert deferred_payload_data["requestor_model_name"] == "account.user"
    assert deferred_payload_data["requestor_object_id"] == staff_user.pk
    assert call_kwargs["kwargs"]["event_delivery_ids"] == [delivery.id]

    assert delivery.event_type == event_type
    assert delivery.payload is None
    assert delivery.webhook == webhook


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport"
    ".send_webhook_request_async.apply_async"
)
def test_generate_deferred_payload_with_dataclass(
    mocked_send_webhook_request_async,
    variant_with_many_stocks,
    channel_USD,
    subscription_webhook,
    staff_user,
):
    # given
    variant = variant_with_many_stocks
    variant_global_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED

    webhook = subscription_webhook(PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED, event_type)

    previous_price = Decimal("10.00")
    new_price = Decimal("8.00")
    currency = channel_USD.currency_code

    deferred_payload_data = DeferredPayloadData(
        subscribable_object_data={
            "variant_id": variant.id,
            "channel_id": channel_USD.id,
            "channel_slug": channel_USD.slug,
            "previous_price_amount": str(previous_price),
            "new_price_amount": str(new_price),
            "currency": currency,
        },
        requestor_model_name="account.user",
        requestor_object_id=staff_user.pk,
        request_time=None,
    )
    delivery = EventDelivery(
        event_type=event_type,
        webhook=webhook,
        status=EventDeliveryStatus.PENDING,
    )
    delivery.save()

    # when
    generate_deferred_payloads(
        event_delivery_ids=[delivery.pk],
        deferred_payload_data=asdict(deferred_payload_data),
    )

    # then
    delivery.refresh_from_db()
    assert delivery.payload

    payload = json.loads(delivery.payload.get_payload())
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    assert payload["productVariant"]["id"] == variant_global_id
    assert payload["productVariant"]["pricing"]["price"]["gross"]["amount"] == (
        variant_channel_listing.discounted_price_amount
    )
    assert payload["channel"]["slug"] == channel_USD.slug
    assert payload["previousPrice"] == {
        "amount": float(previous_price),
        "currency": currency,
    }
    assert payload["newPrice"] == {
        "amount": float(new_price),
        "currency": currency,
    }

    assert mocked_send_webhook_request_async.call_count == 1
    call_kwargs = mocked_send_webhook_request_async.call_args.kwargs
    assert call_kwargs["kwargs"]["event_delivery_id"] == delivery.pk


def test_reconstruct_subscribable_object_with_invalid_data():
    # given
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED
    deferred_data = DeferredPayloadData(
        subscribable_object_data={"variant_id": 1, "unexpected_field": "value"},
        requestor_model_name=None,
        requestor_object_id=None,
        request_time=None,
    )

    # when / then
    with pytest.raises(ValueError, match="Failed to reconstruct"):
        _reconstruct_subscribable_object(event_type, deferred_data)


def test_reconstruct_subscribable_object_with_unregistered_event_type():
    # given
    deferred_data = DeferredPayloadData(
        subscribable_object_data={"variant_id": 1},
        requestor_model_name=None,
        requestor_object_id=None,
        request_time=None,
    )

    # when / then
    with pytest.raises(ValueError, match="No subscribable object class registered"):
        _reconstruct_subscribable_object("unregistered_event_type", deferred_data)
