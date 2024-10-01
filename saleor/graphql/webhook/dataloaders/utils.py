from collections import defaultdict
from typing import TYPE_CHECKING, Optional

from ....webhook.utils import get_webhooks_for_event
from ...app.dataloaders import AppByIdLoader
from ...core import SaleorContext
from ...core.dataloaders import DataLoader
from ...utils import get_user_or_app_from_context
from ..subscription_payload import initialize_request

if TYPE_CHECKING:
    from ....webhook.models import Webhook


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


class AppByEventTypeLoader(DataLoader):
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
            WebhookByEventTypeLoader(self.context)
            .load_many(keys)
            .then(return_apps_for_webhooks)
        )


class WebhookByEventTypeLoader(DataLoader):
    context_key = "webhook_by_event_type"

    def batch_load(self, keys):
        webhooks_by_event_type: dict[str, list[Webhook]] = defaultdict(list)
        for event_type in keys:
            webhooks = get_webhooks_for_event(event_type)
            webhooks_by_event_type[event_type] = list(webhooks)
        return [webhooks_by_event_type.get(event_type) for event_type in keys]
