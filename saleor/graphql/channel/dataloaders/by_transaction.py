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
        transaction_item_ids = list(keys)

        transaction_items_with_order_ids_only = (
            TransactionItem.objects.using(self.database_connection_name)
            .only("order_id", "checkout_id", "id")
            .in_bulk(transaction_item_ids)
        )

        orders_ref_dict = {
            item.id: item.order_id
            for item in transaction_items_with_order_ids_only.values()
            if item.order_id
        }

        checkouts_ref_dict = {
            item.id: item.checkout_id
            for item in transaction_items_with_order_ids_only.values()
            if item.checkout_id
        }

        # Get unique order IDs and checkout IDs to load
        order_ids_to_load = [
            order_id
            for transaction_id in transaction_item_ids
            if (order_id := orders_ref_dict.get(transaction_id)) is not None
        ]

        checkout_ids_to_load = [
            checkout_id
            for transaction_id in transaction_item_ids
            if (checkout_id := checkouts_ref_dict.get(transaction_id)) is not None
        ]

        # Resolve flatten channels and maintain order
        def with_loaded_data(loaded_data):
            checkout_channels, order_channels = loaded_data

            # Create lookup maps
            order_id_to_channel = {}
            for i, order_id in enumerate(order_ids_to_load):
                if i < len(order_channels):
                    order_id_to_channel[order_id] = order_channels[i]

            checkout_id_to_channel = {}
            for i, checkout_id in enumerate(checkout_ids_to_load):
                if i < len(checkout_channels):
                    checkout_id_to_channel[checkout_id] = checkout_channels[i]

            # Map each transaction ID to its channel
            result = []
            for transaction_id in transaction_item_ids:
                channel = None
                if transaction_id in orders_ref_dict:
                    order_id = orders_ref_dict[transaction_id]
                    channel = order_id_to_channel.get(order_id)
                elif transaction_id in checkouts_ref_dict:
                    checkout_id = checkouts_ref_dict[transaction_id]
                    channel = checkout_id_to_channel.get(checkout_id)
                result.append(channel)

            return result

        by_checkout_promise = ChannelByCheckoutIDLoader(self.context).load_many(
            checkout_ids_to_load
        )
        by_order_promise = ChannelByOrderIdLoader(self.context).load_many(
            order_ids_to_load
        )

        return Promise.all([by_checkout_promise, by_order_promise]).then(
            with_loaded_data
        )
