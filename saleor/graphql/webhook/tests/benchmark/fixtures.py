from itertools import cycle

import pytest

from .....app.models import App
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.models import Webhook, WebhookEvent

NUMBER_OF_WEBHOOKS_PER_APP = 6


def _prepare_async_and_sync_events(webhook):
    return [
        WebhookEvent(
            webhook=webhook, event_type=WebhookEventSyncType.PAYMENT_AUTHORIZE
        ),
        WebhookEvent(webhook=webhook, event_type=WebhookEventAsyncType.ANY),
    ]


def _prepare_sync_event(webhook):
    return [
        WebhookEvent(
            webhook=webhook,
            event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        )
    ]


def _prepare_async_event(webhook):
    return [
        WebhookEvent(webhook=webhook, event_type=WebhookEventAsyncType.CHANNEL_CREATED)
    ]


@pytest.fixture
def events_cycle():
    return cycle(
        (
            _prepare_async_and_sync_events,
            _prepare_sync_event,
            _prepare_async_event,
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


@pytest.fixture
def apps_without_webhooks(db):
    return App.objects.bulk_create(
        [
            App(name="App1", is_active=True),
            App(name="App2", is_active=False),
            App(name="App3", is_active=True),
            App(name="App4", is_active=False),
        ]
    )


@pytest.fixture
def webhooks_without_events(apps_without_webhooks):
    webhooks = []

    for app in apps_without_webhooks[:2]:
        for index in range(NUMBER_OF_WEBHOOKS_PER_APP):
            webhook = Webhook(
                name=f"Webhook_{index}",
                app=app,
                target_url=f"http://localhost/test_{index}",
                is_active=index % 2,
            )
            webhooks.append(webhook)

    return Webhook.objects.bulk_create(webhooks)
