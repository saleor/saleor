from unittest.mock import patch

import pytest

from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.utils import get_webhooks_for_multiple_events
from ..events import (
    call_event,
    call_event_including_protected_events,
    validate_async_event,
)


def test_call_event_cannot_be_used_with_checkout_info_object(
    checkout_info, plugins_manager
):
    with pytest.raises(NotImplementedError):
        call_event(plugins_manager.checkout_updated, checkout_info)


def test_call_event_cannot_be_used_with_checkout_object(checkout, plugins_manager):
    with pytest.raises(NotImplementedError):
        call_event(plugins_manager.checkout_updated, checkout)


def test_validate_async_event_requires_event_in_map():
    # given
    event_name = WebhookEventAsyncType.ORDER_CREATED
    webhook_event_map = {}

    # when & then
    with pytest.raises(
        ValueError, match=f"Event {event_name} not found in webhook_event_map."
    ):
        validate_async_event(event_name, webhook_event_map, [])


def test_validate_async_event_not_async_event():
    # given
    event_name = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    webhook_event_map = {}

    # when & then
    with pytest.raises(ValueError, match=f"Event {event_name} is not an async event."):
        validate_async_event(event_name, webhook_event_map, [])


def test_validate_async_event_missing_event_in_map():
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
        validate_async_event(
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
