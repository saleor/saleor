from collections import defaultdict

from ...core.models import EventPayload
from ...webhook.models import WebhookEvent
from ..core.dataloaders import DataLoader


class PayloadByIdLoader(DataLoader[str, str]):
    context_key = "payload_by_id"

    def batch_load(self, keys):
        payload = EventPayload.objects.using(self.database_connection_name).in_bulk(
            keys
        )

        return [
            payload[payload_id].payload if payload.get(payload_id) else None
            for payload_id in keys
        ]


class WebhookEventsByWebhookIdLoader(DataLoader):
    context_key = "webhook_events_by_webhook_id"

    def batch_load(self, keys):
        webhook_events = WebhookEvent.objects.using(
            self.database_connection_name
        ).filter(webhook_id__in=keys)

        webhook_events_map = defaultdict(list)
        for event in webhook_events:
            webhook_events_map[event.webhook_id].append(event)

        return [webhook_events_map.get(webhook_id, []) for webhook_id in keys]
