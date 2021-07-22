from ...app.models import App
from ..core.dataloaders import DataLoader


class AppByIdLoader(DataLoader):
    context_key = "channel_by_id"

    def batch_load(self, keys):
        channels = App.objects.in_bulk(keys)
        return [channels.get(channel_id) for channel_id in keys]
