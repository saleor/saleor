from collections import defaultdict

from django.db.models import Exists, OuterRef

from ...channel.models import Channel
from ...order.models import Order
from ...shipping.models import ShippingZone
from ..checkout.dataloaders import CheckoutByIdLoader, CheckoutLineByIdLoader
from ..core.dataloaders import DataLoader
from ..order.dataloaders import OrderByIdLoader, OrderLineByIdLoader
from ..shipping.dataloaders import ShippingZoneByIdLoader


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


class ChannelByCheckoutLineIDLoader(DataLoader):
    context_key = "channel_by_checkout_line"

    def batch_load(self, keys):
        def channel_by_lines(checkout_lines):
            checkout_ids = [line.checkout_id for line in checkout_lines]

            def channels_by_checkout(checkouts):
                channel_ids = [checkout.channel_id for checkout in checkouts]

                return ChannelByIdLoader(self.context).load_many(channel_ids)

            return (
                CheckoutByIdLoader(self.context)
                .load_many(checkout_ids)
                .then(channels_by_checkout)
            )

        return (
            CheckoutLineByIdLoader(self.context).load_many(keys).then(channel_by_lines)
        )


class ChannelByOrderLineIdLoader(DataLoader):
    context_key = "channel_by_orderline"

    def batch_load(self, keys):
        def channel_by_lines(order_lines):
            order_ids = [line.order_id for line in order_lines]

            def channels_by_checkout(orders):
                channel_ids = [order.channel_id for order in orders]

                return ChannelByIdLoader(self.context).load_many(channel_ids)

            return (
                OrderByIdLoader(self.context)
                .load_many(order_ids)
                .then(channels_by_checkout)
            )

        return OrderLineByIdLoader(self.context).load_many(keys).then(channel_by_lines)


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


class ShippingZonesByChannelIdLoader(DataLoader):
    context_key = "shippingzone_by_channel"

    def batch_load(self, keys):
        zone_and_channel_is_pairs = (
            ShippingZone.objects.using(self.database_connection_name)
            .filter(channels__id__in=keys)
            .values_list("pk", "channels__id")
        )
        channel_shipping_zone_map = defaultdict(list)
        for zone_id, channel_id in zone_and_channel_is_pairs:
            channel_shipping_zone_map[channel_id].append(zone_id)

        def map_shipping_zones(shipping_zones):
            zone_map = {zone.pk: zone for zone in shipping_zones}
            return [
                [zone_map[zone_id] for zone_id in channel_shipping_zone_map[channel_id]]
                for channel_id in keys
            ]

        return (
            ShippingZoneByIdLoader(self.context)
            .load_many({pk for pk, _ in zone_and_channel_is_pairs})
            .then(map_shipping_zones)
        )
