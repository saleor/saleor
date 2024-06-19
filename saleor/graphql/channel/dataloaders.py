from django.db.models import Exists, OuterRef

from ...channel.models import Channel
from ...order.models import Order
from ..core.dataloaders import DataLoader
from ..order.dataloaders import OrderByIdLoader


class ChannelByIdLoader(DataLoader):
    context_key = "channel_by_id"

    def batch_load(self, keys):
        channels = Channel.objects.using(self.database_connection_name).in_bulk(keys)
        return [channels.get(channel_id) for channel_id in keys]


class ChannelBySlugLoader(DataLoader):
    context_key = "channel_by_slug"

    def batch_load(self, keys):
        channels = Channel.objects.using(self.database_connection_name).in_bulk(
            keys, field_name="slug"
        )
        return [channels.get(slug) for slug in keys]


class ChannelByOrderIdLoader(DataLoader):
    context_key = "channel_by_order"

    def batch_load(self, keys):
        def with_orders(orders):
            def with_channels(channels):
                channel_map = {channel.id: channel for channel in channels}
                return [
                    channel_map.get(order.channel_id) if order else None
                    for order in orders
                ]

            channel_ids = set(order.channel_id for order in orders if order)
            return (
                ChannelByIdLoader(self.context)
                .load_many(channel_ids)
                .then(with_channels)
            )

        return OrderByIdLoader(self.context).load_many(keys).then(with_orders)


class ChannelWithHasOrdersByIdLoader(DataLoader):
    context_key = "channel_with_has_orders_by_id"

    def batch_load(self, keys):
        orders = Order.objects.using(self.database_connection_name).filter(
            channel=OuterRef("pk")
        )
        channels = (
            Channel.objects.using(self.database_connection_name)
            .annotate(has_orders=Exists(orders))
            .in_bulk(keys)
        )
        return [channels.get(channel_id) for channel_id in keys]
