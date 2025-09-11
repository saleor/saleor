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
        transaction_item_ids = keys

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
