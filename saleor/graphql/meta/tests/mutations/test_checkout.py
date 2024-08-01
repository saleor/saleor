from datetime import timedelta
from unittest.mock import call, patch

import graphene
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....checkout.actions import call_checkout_event_for_checkout_info
from .....core.models import EventDelivery
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_delete_public_metadata_for_checkout(api_client, checkout):
    # given
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.metadata_storage.save(update_fields=["metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_public_metadata_for_checkout_by_token(api_client, checkout):
    # given
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.metadata_storage.save(update_fields=["metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout.token, "Checkout"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_public_metadata_for_checkout_line(api_client, checkout_line):
    # given
    checkout_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout_line.save(update_fields=["metadata"])
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_line_id, "CheckoutLine"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], checkout_line, checkout_line_id
    )


def test_delete_private_metadata_for_checkout(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE}
    )
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_private_metadata_for_checkout_by_token(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE}
    )
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout.token, "Checkout"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_private_metadata_for_checkout_line(
    staff_api_client, checkout_line, permission_manage_checkouts
):
    # given
    checkout_line.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    checkout_line.save(update_fields=["private_metadata"])
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_line_id, "CheckoutLine"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout_line,
        checkout_line_id,
    )


def test_add_public_metadata_for_checkout(api_client, checkout):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_add_public_metadata_for_checkout_no_checkout_metadata_storage(
    api_client, checkout
):
    # given
    checkout.metadata_storage.delete()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    checkout.refresh_from_db()
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_add_public_metadata_for_checkout_line(api_client, checkout_line):
    # given
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_line_id, "CheckoutLine"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], checkout_line, checkout_line_id
    )


def test_add_public_metadata_for_checkout_by_token(api_client, checkout):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout.token, "Checkout"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_add_metadata_for_checkout_triggers_checkout_updated_hook(
    mock_checkout_updated, api_client, checkout
):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert response["data"]["updateMetadata"]["errors"] == []
    mock_checkout_updated.assert_called_once_with(checkout)


def test_add_private_metadata_for_checkout(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_add_private_metadata_for_checkout_no_checkout_metadata_storage(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.delete()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    checkout.refresh_from_db()
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_add_private_metadata_for_checkout_line(
    staff_api_client, checkout_line, permission_manage_checkouts
):
    # given
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_line_id, "CheckoutLine"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout_line,
        checkout_line_id,
    )


def test_add_private_metadata_for_checkout_by_token(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout.token, "Checkout"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_update_private_metadata_for_checkout_line(
    staff_api_client, checkout_line, permission_manage_checkouts
):
    # given
    checkout_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout_line.save(update_fields=["private_metadata"])
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout_line_id,
        "CheckoutLine",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout_line,
        checkout_line_id,
        value="NewMetaValue",
    )


def test_update_public_metadata_for_checkout_line(api_client, checkout_line):
    # given
    checkout_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout_line.save(update_fields=["metadata"])
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_line_id, "CheckoutLine", value="NewMetaValue"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        checkout_line,
        checkout_line_id,
        value="NewMetaValue",
    )


@freeze_time("2023-05-31 12:00:01")
@patch(
    "saleor.graphql.meta.extra_methods.call_checkout_event_for_checkout_info",
    wraps=call_checkout_event_for_checkout_info,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_add_metadata_for_checkout_triggers_webhooks_with_checkout_updated(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event_for_checkout,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    checkout.price_expiration = timezone.now() - timedelta(hours=10)
    checkout.save(update_fields=["price_expiration"])
    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert response["data"]["updateMetadata"]["errors"] == []

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
    assert wrapped_call_checkout_event_for_checkout.called


@freeze_time("2023-05-31 12:00:01")
@patch(
    "saleor.graphql.meta.extra_methods.call_checkout_event_for_checkout_info",
    wraps=call_checkout_event_for_checkout_info,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_add_metadata_for_checkout_triggers_webhooks_with_updated_metadata(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event_for_checkout,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_metadata_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED)

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    checkout.price_expiration = timezone.now() - timedelta(hours=10)
    checkout.save(update_fields=["price_expiration"])

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert response["data"]["updateMetadata"]["errors"] == []

    # confirm that event delivery was generated for each webhook.
    checkout_metadata_updated_delivery = EventDelivery.objects.get(
        webhook_id=checkout_metadata_updated_webhook.id
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
        kwargs={"event_delivery_id": checkout_metadata_updated_delivery.id},
        queue=None,
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
    assert wrapped_call_checkout_event_for_checkout.called
