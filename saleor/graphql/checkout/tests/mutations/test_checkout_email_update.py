from unittest.mock import patch

from django.test import override_settings

from .....checkout.actions import call_checkout_event
from .....checkout.error_codes import CheckoutErrorCode
from .....core.models import EventDelivery
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

CHECKOUT_EMAIL_UPDATE_MUTATION = """
    mutation checkoutEmailUpdate($id: ID, $email: String!) {
        checkoutEmailUpdate(id: $id, email: $email) {
            checkout {
                id,
                email
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


def test_checkout_email_update(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])
    previous_last_change = checkout.last_change

    email = "test@example.com"
    variables = {"id": to_global_id_or_none(checkout), "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email
    assert checkout.last_change != previous_last_change


def test_checkout_email_update_when_variant_without_channel_listing(
    user_api_client, checkout_with_item
):
    # given
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])
    previous_last_change = checkout.last_change

    line = checkout.lines.first()
    line.variant.channel_listings.all().delete()

    email = "test@example.com"
    variables = {"id": to_global_id_or_none(checkout), "email": email}

    # when
    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email
    assert checkout.last_change != previous_last_change


def test_checkout_email_update_validation(user_api_client, checkout_with_item):
    variables = {"id": to_global_id_or_none(checkout_with_item), "email": ""}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    previous_last_change = checkout_with_item.last_change

    errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_with_item.last_change == previous_last_change


def test_with_active_problems_flow(api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "email": "admin@example.com",
    }

    # when
    response = api_client.post_graphql(
        CHECKOUT_EMAIL_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutEmailUpdate"]["errors"]


@patch(
    "saleor.graphql.checkout.mutations.checkout_email_update.call_checkout_event",
    wraps=call_checkout_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_email_update_triggers_webhooks(
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

    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])

    email = "test@example.com"
    variables = {"id": to_global_id_or_none(checkout), "email": email}

    # when
    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutEmailUpdate"]["errors"]

    assert wrapped_call_checkout_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": checkout_update_delivery.id},
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )
    assert shipping_methods_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id
