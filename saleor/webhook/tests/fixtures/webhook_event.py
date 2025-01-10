from itertools import cycle

import pytest

from ....webhook.models import WebhookEvent
from .utils import (
    prepare_async_and_sync_events,
    prepare_async_event,
    prepare_sync_event,
)


@pytest.fixture
def events_cycle():
    return cycle(
        (
            prepare_async_and_sync_events,
            prepare_sync_event,
            prepare_async_event,
            lambda x: [],
            lambda x: [],
        )
    )


@pytest.fixture
def webhook_events(webhooks_without_events, events_cycle):
    webhook_events = []

    for webhook in webhooks_without_events:
        webhook_events.extend(next(events_cycle)(webhook))

    return WebhookEvent.objects.bulk_create(webhook_events)
