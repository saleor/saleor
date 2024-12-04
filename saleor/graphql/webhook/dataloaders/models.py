from collections import defaultdict

from ....core.models import EventPayload
from ....webhook.models import Webhook, WebhookEvent
from ...core.dataloaders import DataLoader


class PayloadByIdLoader(DataLoader[str, str]):
    context_key = "payload_by_id"

    def batch_load(self, keys):
        payloads = EventPayload.objects.using(self.database_connection_name).in_bulk(
            keys
        )

        return [
            payloads[payload_id].get_payload() if payloads.get(payload_id) else None
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


class WebhooksByAppIdLoader(DataLoader):
    context_key = "webhooks_by_app_id"

    def batch_load(self, keys):
        webhooks = Webhook.objects.using(self.database_connection_name).filter(
            app_id__in=keys
        )
        webhooks_by_app_map = defaultdict(list)
        for webhook in webhooks:
            webhooks_by_app_map[webhook.app_id].append(webhook)
        return [webhooks_by_app_map.get(app_id, []) for app_id in keys]


class WebhookEventsByEventTypeLoader(DataLoader):
    context_key = "webhook_events_by_event_type"

    def batch_load(self, keys):
        webhook_events_by_event_type: dict[str, list[WebhookEvent]] = defaultdict(list)
        webhooks_events = WebhookEvent.objects.using(
            self.database_connection_name
        ).filter(event_type__in=keys)
        for webhook_event in webhooks_events:
            webhook_events_by_event_type[webhook_event.event_type].append(webhook_event)
        return [webhook_events_by_event_type[event_type] for event_type in keys]


class ActiveWebhooksByIdLoader(DataLoader):
    context_key = "active_webhooks_by_id"

    def batch_load(self, keys):
        webhooks_map = (
            Webhook.objects.using(self.database_connection_name)
            .filter(is_active=True)
            .in_bulk(keys)
        )
        return [webhooks_map.get(webhook_id) for webhook_id in keys]
