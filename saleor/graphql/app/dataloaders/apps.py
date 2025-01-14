from collections import defaultdict

from ....app.models import App
from ...core.dataloaders import DataLoader
from ...webhook.dataloaders.models import WebhooksByEventTypeLoader
from .app import AppByIdLoader


class ActiveAppsByAppIdentifierLoader(DataLoader[str, App]):
    context_key = "apps_by_app_identifier"

    def batch_load(self, keys):
        apps = App.objects.using(self.database_connection_name).filter(
            identifier__in=keys, is_active=True, removed_at__isnull=True
        )
        apps_map = defaultdict(list)
        for app in apps:
            apps_map[app.identifier].append(app)
        return [apps_map.get(app_identifier, []) for app_identifier in keys]


class AppsByEventTypeLoader(DataLoader):
    context_key = "app_by_event_type"

    def batch_load(self, keys):
        app_ids_by_event_type: dict[str, list[int]] = defaultdict(list)
        app_ids = set()

        def return_apps_for_webhooks(webhooks_by_event_type):
            for event_type, webhooks in zip(keys, webhooks_by_event_type, strict=False):
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
