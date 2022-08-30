from collections import defaultdict

from ...app.models import App, AppExtension
from ..core.dataloaders import DataLoader


class AppByIdLoader(DataLoader):
    context_key = "app_by_id"

    def batch_load(self, keys):
        apps = App.objects.using(self.database_connection_name).in_bulk(keys)
        return [apps.get(key) for key in keys]


class AppExtensionByIdLoader(DataLoader):
    context_key = "app_extension_by_id"

    def batch_load(self, keys):
        extensions = AppExtension.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [extensions.get(key) for key in keys]


class AppExtensionByAppIdLoader(DataLoader):
    context_key = "app_extension_by_app_id"

    def batch_load(self, keys):
        extensions = AppExtension.objects.using(self.database_connection_name).filter(
            app_id__in=keys
        )
        extensions_map = defaultdict(list)
        app_extension_loader = AppExtensionByIdLoader(self.context)
        for extension in extensions.iterator():
            extensions_map[extension.app_id].append(extension)
            app_extension_loader.prime(extension.id, extension)
        return [extensions_map.get(app_id, []) for app_id in keys]
