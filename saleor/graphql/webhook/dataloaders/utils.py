from collections import defaultdict
from typing import Optional

from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import (
    calculate_webhooks_for_multiple_events,
)
from ...app.dataloaders import ActiveAppByIdLoader, AppByIdLoader
from ...core import SaleorContext
from ...core.dataloaders import DataLoader
from ...utils import get_user_or_app_from_context
from ..subscription_payload import initialize_request
from .models import ActiveWebhooksByIdLoader, WebhookEventsByEventTypeLoader


class PayloadsRequestContextByEventTypeLoader(DataLoader):
    context_key = "payloads_request_context_by_event_type"

    def batch_load(self, keys):
        request_context_by_event_type: dict[str, Optional[SaleorContext]] = (
            defaultdict()
        )
        requestor = get_user_or_app_from_context(self.context)
        for event_type in keys:
            request_context_by_event_type[event_type] = initialize_request(
                requestor,
                sync_event=True,
                allow_replica=False,
                event_type=event_type,
            )
        return [request_context_by_event_type.get(event_type) for event_type in keys]


class AppsByEventTypeLoader(DataLoader):
    context_key = "app_by_event_type"

    def batch_load(self, keys):
        app_ids_by_event_type: dict[str, list[int]] = defaultdict(list)
        app_ids = set()

        def return_apps_for_webhooks(webhooks):
            for event_type, webhooks in zip(keys, webhooks):
                ids = [webhook.app_id for webhook in webhooks]
                app_ids_by_event_type[event_type] = ids
                app_ids.update(ids)

            def return_apps(
                apps, app_ids_by_event_type=app_ids_by_event_type, keys=keys
            ):
                apps_by_event_type = defaultdict(list)
                app_by_id = defaultdict(list)
                for app in apps:
                    app_by_id[app.id] = app
                for event_type in keys:
                    for app_id in app_ids_by_event_type[event_type]:
                        apps_by_event_type[event_type].append(app_by_id[app_id])
                return [apps_by_event_type[event_type] for event_type in keys]

            return AppByIdLoader(self.context).load_many(app_ids).then(return_apps)

        return (
            WebhooksByEventTypeLoader(self.context)
            .load_many(keys)
            .then(return_apps_for_webhooks)
        )


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
                app_ids = {webhook.app_id for webhook in webhooks}

                def return_webhooks_by_event_type(
                    apps,
                    set_event_types=set_event_types,
                    events_types_by_webhook_id_map=events_types_by_webhook_id_map,
                    webhooks=webhooks,
                ):
                    apps_by_id = {app.id: app for app in apps}
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
