from ....channel.models import Channel
from ...core.dataloaders import DataLoader


class ChannelByIdLoader(DataLoader[int, Channel]):
    context_key = "channel_by_id"

    def batch_load(self, keys):
        channels = Channel.objects.using(self.database_connection_name).in_bulk(keys)
        return [channels.get(channel_id) for channel_id in keys]


class ChannelBySlugLoader(DataLoader[str, Channel]):
    context_key = "channel_by_slug"

    def batch_load(self, keys):
        channels = Channel.objects.using(self.database_connection_name).in_bulk(
            keys, field_name="slug"
        )
        return [channels.get(slug) for slug in keys]
