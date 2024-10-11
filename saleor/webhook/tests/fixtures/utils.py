from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.models import WebhookEvent


def prepare_async_and_sync_events(webhook):
    return [
        WebhookEvent(
            webhook=webhook, event_type=WebhookEventSyncType.PAYMENT_AUTHORIZE
        ),
        WebhookEvent(webhook=webhook, event_type=WebhookEventAsyncType.ANY),
    ]


def prepare_sync_event(webhook):
    return [
        WebhookEvent(
            webhook=webhook,
            event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        )
    ]


def prepare_async_event(webhook):
    return [
        WebhookEvent(webhook=webhook, event_type=WebhookEventAsyncType.CHANNEL_CREATED)
    ]
