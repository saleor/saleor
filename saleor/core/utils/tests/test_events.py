import pytest

from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.utils import get_webhooks_for_multiple_events
from ..events import call_event, webhook_async_event_requires_sync_webhooks_to_trigger


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


def test_webhook_async_event_requires_sync_webhooks_to_trigger():
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
