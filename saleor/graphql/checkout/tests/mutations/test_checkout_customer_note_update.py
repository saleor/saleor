from unittest.mock import call, patch

import before_after
import pytest
from django.db import DatabaseError, OperationalError
from django.test import override_settings

from saleor.checkout.actions import call_checkout_event
from saleor.checkout.error_codes import CheckoutErrorCode
from saleor.checkout.models import Checkout
from saleor.core.models import EventDelivery
from saleor.webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType

from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION = """
    mutation checkoutCustomerNoteUpdate($id: ID!, $customerNote: String!) {
        checkoutCustomerNoteUpdate(id: $id, customerNote: $customerNote) {
            checkout {
                id,
                note
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
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_customer_note_update_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event,
    setup_checkout_webhooks,
    settings,
    user_api_client,
    checkout_with_item,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

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

    # confirm that event delivery was generated for each webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )
    tax_delivery = EventDelivery.objects.get(webhook_id=tax_webhook.id)
    shipping_methods_delivery = EventDelivery.objects.get(
        webhook_id=shipping_webhook.id,
        event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )
    filter_shipping_delivery = EventDelivery.objects.get(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": checkout_update_delivery.id},
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    mocked_send_webhook_request_sync.assert_has_calls(
        [
            call(shipping_methods_delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT),
            call(filter_shipping_delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT),
            call(tax_delivery),
        ]
    )
    assert wrapped_call_checkout_event.called


def test_checkout_customer_note_update_deleted_database_error(
    user_api_client,
    checkout_with_item,
    customer_user2,
    permission_impersonate_user,
):
    # given
    checkout_with_item.email = "old@email.com"
    checkout_with_item.save(update_fields=["email"])
    variables = {"id": to_global_id_or_none(checkout_with_item), "customerNote": "note"}

    # when
    with before_after.before(
        (
            "saleor.graphql.checkout.mutations."
            "checkout_customer_note_update.save_checkout_with_update_fields"
        ),
        lambda *args, **kwargs: Checkout.objects.all().delete(),
    ):
        response = user_api_client.post_graphql(
            CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION, variables
        )
    # then
    data = get_graphql_content(response)["data"]["checkoutCustomerNoteUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "checkout"
    assert errors[0]["message"] == "Checkout does no longer exists."
    assert errors[0]["code"] == CheckoutErrorCode.DELETED.name


@pytest.mark.parametrize("error", [OperationalError, DatabaseError])
def test_checkout_customer_note_update_raise_error_which_inherits_from_database_error(
    user_api_client,
    checkout_with_item,
    customer_user2,
    permission_impersonate_user,
    error,
):
    # given
    checkout_with_item.email = "old@email.com"
    checkout_with_item.save(update_fields=["email"])
    variables = {"id": to_global_id_or_none(checkout_with_item), "customerNote": "note"}

    # when
    with patch.object(Checkout, "save", side_effect=error):
        response = user_api_client.post_graphql(
            CHECKOUT_CUSTOMER_NOTE_UPDATE_MUTATION, variables
        )

    # then
    data = get_graphql_content(response, ignore_errors=True)
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["message"] == "Internal Server Error"
    assert errors[0]["extensions"]["exception"]["code"] == error.__name__
