from unittest.mock import ANY, patch

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....checkout.actions import call_checkout_event
from .....core.models import EventDelivery
from .....product.models import ProductChannelListing, ProductVariantChannelListing
from .....webhook.event_types import WebhookEventAsyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION = """
    mutation checkoutCustomerNoteUpdate($id: ID!, $customerNote: String!) {
        checkoutCustomerNoteUpdate(id: $id, customerNote: $customerNote) {
            checkout {
                id,
                note
                customerNote
            },
            errors {
                field,
                message
            }
            errors {
                field,
                message
                code
            }
        }
    }
"""


def test_checkout_customer_note_update(user_api_client, checkout_with_item):
    # given
    checkout = checkout_with_item
    checkout.note = ""
    checkout.save(update_fields=["note"])
    previous_last_change = checkout.last_change

    customer_note = "New customer note value"
    variables = {"id": to_global_id_or_none(checkout), "customerNote": customer_note}

    # when
    response = user_api_client.post_graphql(
        CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerNoteUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.note == customer_note
    assert data["checkout"]["customerNote"] == data["checkout"]["note"] == customer_note
    assert checkout.last_change != previous_last_change


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_customer_note_update_when_line_without_listing(
    channel_listing_model, listing_filter_field, user_api_client, checkout_with_item
):
    # given
    checkout = checkout_with_item
    checkout.note = ""
    checkout.save(update_fields=["note"])
    previous_last_change = checkout.last_change

    line = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id, **{listing_filter_field: line.variant_id}
    ).delete()

    customer_note = "New customer note value"
    variables = {"id": to_global_id_or_none(checkout), "customerNote": customer_note}

    # when
    response = user_api_client.post_graphql(
        CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerNoteUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.note == customer_note
    assert data["checkout"]["customerNote"] == data["checkout"]["note"] == customer_note
    assert checkout.last_change != previous_last_change


def test_with_active_problems_flow(api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "customerNote": "New customer note value",
    }

    # when
    response = api_client.post_graphql(
        CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutCustomerNoteUpdate"]["errors"]


@patch(
    "saleor.graphql.checkout.mutations.checkout_customer_note_update.call_checkout_event",
    wraps=call_checkout_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_customer_note_update_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event,
    setup_checkout_webhooks,
    settings,
    user_api_client,
    checkout_with_item,
    address,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_item.shipping_address = address
    checkout_with_item.billing_address = address

    checkout_with_item.save()

    customer_note = "New customer note value"
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "customerNote": customer_note,
    }

    # when
    response = user_api_client.post_graphql(
        CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerNoteUpdate"]
    assert not data["errors"]

    assert wrapped_call_checkout_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout_with_item.pk,
                "requestor_model_name": "account.user",
                "requestor_object_id": user_api_client.user.pk,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the sync and async actions
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2024-05-31 12:00:01")
def test_checkout_customer_note_update_do_not_mark_shipping_as_stale(
    user_api_client, checkout_with_item, checkout_delivery, address
):
    # given
    expected_stale_time = timezone.now() + timezone.timedelta(minutes=10)

    checkout = checkout_with_item
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = expected_stale_time
    checkout.save(
        update_fields=[
            "assigned_delivery",
            "shipping_address",
            "delivery_methods_stale_at",
        ]
    )

    customer_note = "New customer note value"
    variables = {"id": to_global_id_or_none(checkout), "customerNote": customer_note}

    # when
    new_now = timezone.now() + timezone.timedelta(minutes=1)
    with freeze_time(new_now):
        response = user_api_client.post_graphql(
            CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION, variables
        )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerNoteUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.delivery_methods_stale_at == expected_stale_time
