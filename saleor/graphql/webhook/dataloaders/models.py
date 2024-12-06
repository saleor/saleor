from collections import defaultdict

from ....core.models import EventPayload
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook, WebhookEvent
from ....webhook.utils import (
    calculate_webhooks_for_multiple_events,
)
from ...app.dataloaders import ActiveAppByIdLoader
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


class WebhooksByEventTypeLoader(DataLoader):
    context_key = "webhooks_by_event_type"

    def batch_load(self, keys):
        set_event_types = set(keys)
        if set_event_types.intersection(WebhookEventAsyncType.ALL):
            set_event_types.add(WebhookEventAsyncType.ANY)

        def fetch_webhooks(
            webhook_events_by_event_types, set_event_types=set_event_types
        ):
            events_types_by_webhook_id_map: dict[int, set[str]] = defaultdict(set)
            webhooks_ids = set()
            for webhook_events_by_event_type in webhook_events_by_event_types:
                for webhook_event in webhook_events_by_event_type:
                    webhooks_id = webhook_event.webhook_id
                    events_types_by_webhook_id_map[webhook_event.webhook_id].add(
                        webhook_event.event_type
                    )
                    webhooks_ids.add(webhooks_id)

            def fetch_apps(
                webhooks,
                set_event_types=set_event_types,
                events_types_by_webhook_id_map=events_types_by_webhook_id_map,
            ):
                # Filter out None values due to webhooks that are not active.
                webhooks = [webhook for webhook in webhooks if webhook]
                app_ids = {webhook.app_id for webhook in webhooks}

                def return_webhooks_by_event_type(
                    apps,
                    set_event_types=set_event_types,
                    events_types_by_webhook_id_map=events_types_by_webhook_id_map,
                    webhooks=webhooks,
                ):
                    apps_by_id = {app.id: app for app in apps if app}
                    webhooks_by_event_type_map = calculate_webhooks_for_multiple_events(
                        set_event_types,
                        apps_by_id,
                        webhooks,
                        events_types_by_webhook_id_map,
                    )
                    return [
                        webhooks_by_event_type_map.get(event_type, [])
                        for event_type in keys
                    ]

                return (
                    ActiveAppByIdLoader(self.context)
                    .load_many(app_ids)
                    .then(return_webhooks_by_event_type)
                )

            return (
                ActiveWebhooksByIdLoader(self.context)
                .load_many(webhooks_ids)
                .then(fetch_apps)
            )

        return (
            WebhookEventsByEventTypeLoader(self.context)
            .load_many(set_event_types)
            .then(fetch_webhooks)
        )
