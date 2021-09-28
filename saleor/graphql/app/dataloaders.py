from ...app.models import App
from ..core.dataloaders import DataLoader


class AppByIdLoader(DataLoader):
    context_key = "app_by_id"

    def batch_load(self, keys):
        apps = App.objects.in_bulk(keys)
        return [apps.get(app_id) for app_id in keys]
