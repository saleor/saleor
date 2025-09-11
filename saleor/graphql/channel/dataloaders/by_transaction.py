from collections.abc import Iterable

from promise import Promise

from ....channel.models import Channel
from ....payment.models import TransactionItem
from ...core.dataloaders import DataLoader
from .by_checkout import ChannelByCheckoutIDLoader
from .by_order import ChannelByOrderIdLoader


class ChannelByTransactionIdLoader(DataLoader[int, Channel]):
    context_key = "channel_by_transaction_id"

    def batch_load(self, keys: Iterable[int]):
        transaction_ids = list(keys)

        transaction_items = (
            TransactionItem.objects.using(self.database_connection_name)
            .only("order_id", "checkout_id", "id")
            .in_bulk(transaction_ids)
        )

        transaction_to_order = {
            item.id: item.order_id
            for item in transaction_items.values()
            if item.order_id
        }

        transaction_to_checkout = {
            item.id: item.checkout_id
            for item in transaction_items.values()
            if item.checkout_id
        }

        order_ids = [
            order_id
            for transaction_id in transaction_ids
            if (order_id := transaction_to_order.get(transaction_id)) is not None
        ]

        checkout_ids = [
            checkout_id
            for transaction_id in transaction_ids
            if (checkout_id := transaction_to_checkout.get(transaction_id)) is not None
        ]

        def resolve_channels(loaded_data):
            checkout_channels, order_channels = loaded_data

            order_to_channel = dict(zip(order_ids, order_channels, strict=False))
            checkout_to_channel = dict(
                zip(checkout_ids, checkout_channels, strict=False)
            )

            def get_channel_for_transaction(transaction_id):
                if order_id := transaction_to_order.get(transaction_id):
                    return order_to_channel.get(order_id)
                if checkout_id := transaction_to_checkout.get(transaction_id):
                    return checkout_to_channel.get(checkout_id)
                return None

            return [get_channel_for_transaction(tid) for tid in transaction_ids]

        checkout_promise = ChannelByCheckoutIDLoader(self.context).load_many(
            checkout_ids
        )
        order_promise = ChannelByOrderIdLoader(self.context).load_many(order_ids)

        return Promise.all([checkout_promise, order_promise]).then(resolve_channels)
