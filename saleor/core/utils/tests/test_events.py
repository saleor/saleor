from unittest.mock import patch

import pytest

from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.utils import get_webhooks_for_multiple_events
from ..events import (
    call_event,
    call_event_including_protected_events,
    webhook_async_event_requires_sync_webhooks_to_trigger,
)


def test_call_event_cannot_be_used_with_checkout_info_object(
    checkout_info, plugins_manager
):
    with pytest.raises(NotImplementedError):
        call_event(plugins_manager.checkout_updated, checkout_info)


def test_call_event_cannot_be_used_with_checkout_object(checkout, plugins_manager):
    with pytest.raises(NotImplementedError):
        call_event(plugins_manager.checkout_updated, checkout)


def test_webhook_async_event_requires_sync_webhooks_to_trigger_requires_event_in_map():
    # given
    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = {}

    # when & then
    with pytest.raises(
        ValueError, match=f"Event {event_name} not found in webhook_event_map."
    ):
        webhook_async_event_requires_sync_webhooks_to_trigger(
            event_name, webhook_event_map, []
        )


def test_webhook_async_event_requires_sync_webhooks_to_trigger_not_async_event():
    # given
    event_name = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    webhook_event_map = {}

    # when & then
    with pytest.raises(ValueError, match=f"Event {event_name} is not an async event."):
        webhook_async_event_requires_sync_webhooks_to_trigger(
            event_name, webhook_event_map, []
        )


def test_webhook_async_event_requires_sync_webhooks_to_trigger_when_no_webhooks():
    # given
    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_CREATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert not should_trigger


def test_webhook_async_event_requires_sync_webhooks_to_trigger_when_async_webhook(
    webhook, permission_manage_orders
):
    # given
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    webhook.app.permissions.set([permission_manage_orders])

    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_CREATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert not should_trigger


def test_webhook_async_event_requires_sync_webhooks_to_trigger_when_sync_webhook_active(
    webhook, permission_manage_orders, setup_order_webhooks
):
    # given
    different_event = WebhookEventAsyncType.ORDER_EXPIRED
    (
        tax_webhook,
        shipping_filter_webhook,
        order_created_webhook,
    ) = setup_order_webhooks(different_event)

    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_CREATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert not should_trigger


def test_webhook_async_event_requires_sync_webhooks_to_trigger_webhooks_active(
    setup_order_webhooks,
):
    # given
    event_name = WebhookEventAsyncType.ORDER_CREATED
    (
        tax_webhook,
        shipping_filter_webhook,
        order_created_webhook,
    ) = setup_order_webhooks(event_name)

    webhook_event_map = get_webhooks_for_multiple_events(
        [event_name, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert should_trigger


def test_webhook_async_event_requires_sync_webhooks_to_trigger_missing_event_in_map():
    # given
    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [
            WebhookEventAsyncType.ORDER_CREATED,
        ]
    )

    # when & then
    with pytest.raises(
        ValueError,
        match=(
            f"Event {set(WebhookEventSyncType.ORDER_EVENTS)} not found in "
            "webhook_event_map."
        ),
    ):
        webhook_async_event_requires_sync_webhooks_to_trigger(
            event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
        )


@patch("saleor.plugins.manager.PluginsManager.checkout_created")
def test_call_event_including_protected_events(
    mocked_checkout_created,
    checkout_with_items,
    plugins_manager,
    webhook,
    django_capture_on_commit_callbacks,
):
    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_event_including_protected_events(
            plugins_manager.checkout_created, checkout_with_items, webhooks=[webhook]
        )

    # then
    mocked_checkout_created.assert_called_once_with(
        checkout_with_items, webhooks=[webhook]
    )


@pytest.mark.parametrize("subscription_query", ["", None])
def test_webhook_async_event_requires_sync_webhooks_to_trigger_no_subscription_for_event(
    setup_order_webhooks, subscription_query, webhook, permission_manage_orders
):
    # given
    (
        tax_webhook,
        shipping_filter_webhook,
        order_created_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.ORDER_CREATED)

    order_created_webhook.subscription_query = subscription_query
    order_created_webhook.save(update_fields=["subscription_query"])

    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    webhook.app.permissions.set([permission_manage_orders])
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])

    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_CREATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert not should_trigger


@pytest.mark.parametrize("subscription_query", ["", None])
def test_webhook_async_event_requires_sync_webhooks_to_trigger_no_subscription_single_webhook(
    setup_order_webhooks, subscription_query, webhook, permission_manage_orders
):
    # given
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    webhook.app.permissions.set([permission_manage_orders])
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])

    (
        tax_webhook,
        shipping_filter_webhook,
        order_created_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.ORDER_CREATED)

    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_CREATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert should_trigger


@pytest.mark.parametrize("subscription_query", ["", None])
def test_webhook_async_event_requires_sync_webhooks_to_trigger_no_subscription_for_async_events(
    setup_order_webhooks, subscription_query
):
    # given
    (
        tax_webhook,
        shipping_filter_webhook,
        order_created_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.ORDER_CREATED)
    tax_webhook.subscription_query = subscription_query
    tax_webhook.save(update_fields=["subscription_query"])
    shipping_filter_webhook.subscription_query = subscription_query
    shipping_filter_webhook.save(update_fields=["subscription_query"])

    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_CREATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert not should_trigger


@pytest.mark.parametrize("subscription_query", ["", None])
def test_webhook_async_event_requires_sync_webhooks_to_trigger_no_subscription_for_single_async_event(
    setup_order_webhooks, subscription_query
):
    # given
    (
        tax_webhook,
        shipping_filter_webhook,
        order_created_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.ORDER_CREATED)
    shipping_filter_webhook.subscription_query = subscription_query
    shipping_filter_webhook.save(update_fields=["subscription_query"])

    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_CREATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    # when

    should_trigger = webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name, webhook_event_map, WebhookEventSyncType.ORDER_EVENTS
    )

    # then
    assert should_trigger
