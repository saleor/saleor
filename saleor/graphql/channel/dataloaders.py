from collections.abc import Iterable
from uuid import UUID

from django.db.models import Exists, OuterRef
from promise import Promise

from ...channel.models import Channel
from ...order.models import Order
from ...payment.models import TransactionItem
from ..checkout.dataloaders import CheckoutByTokenLoader
from ..core.dataloaders import DataLoader
from ..order.dataloaders import OrderByIdLoader


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


class ChannelByOrderIdLoader(DataLoader[UUID, Channel]):
    context_key = "channel_by_order"

    def batch_load(self, keys):
        def with_orders(orders):
            def with_channels(channels):
                channel_map = {channel.id: channel for channel in channels}
                return [
                    channel_map.get(order.channel_id) if order else None
                    for order in orders
                ]

            channel_ids = {order.channel_id for order in orders if order}
            return (
                ChannelByIdLoader(self.context)
                .load_many(channel_ids)
                .then(with_channels)
            )

        return OrderByIdLoader(self.context).load_many(keys).then(with_orders)


class ChannelWithHasOrdersByIdLoader(DataLoader[int, Channel]):
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


class ChannelByCheckoutIDLoader(DataLoader[UUID, Channel]):
    context_key = "channel_by_checkout"

    def batch_load(self, keys):
        def with_checkouts(checkouts):
            def with_channels(channels):
                channel_map = {channel.id: channel for channel in channels}
                return [
                    channel_map.get(checkout.channel_id) if checkout else None
                    for checkout in checkouts
                ]

            channel_ids = {checkout.channel_id for checkout in checkouts if checkout}
            return (
                ChannelByIdLoader(self.context)
                .load_many(channel_ids)
                .then(with_channels)
            )

        return CheckoutByTokenLoader(self.context).load_many(keys).then(with_checkouts)


class ChannelByTransactionIdLoader(DataLoader[int, Channel]):
    context_key = "channel_by_transaction_id"

    def batch_load(self, keys: Iterable[int]):
        transaction_item_ids = keys

        # Order doesn't have relation to transaction item, so we first need to do reverse
        transaction_items_with_order_ids_only = (
            TransactionItem.objects.using(self.database_connection_name)
            .only("order_id", "checkout_id")
            .in_bulk(transaction_item_ids)
        )

        order_ids = [
            item.order_id for item in transaction_items_with_order_ids_only.values()
        ]

        checkout_ids = [
            item.checkout_id for item in transaction_items_with_order_ids_only.values()
        ]

        # TODO Make stable sorting
        by_order_promise = ChannelByOrderIdLoader(self.context).load_many(order_ids)
        by_channel_promise = ChannelByCheckoutIDLoader(self.context).load_many(
            checkout_ids
        )

        return Promise.all([by_channel_promise, by_order_promise])
