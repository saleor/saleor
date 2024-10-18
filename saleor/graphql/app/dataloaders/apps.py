from collections import defaultdict

from ....app.models import App
from ...core.dataloaders import DataLoader


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
