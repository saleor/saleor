from uuid import UUID

from ....channel.models import Channel
from ...checkout.dataloaders import CheckoutByTokenLoader
from ...core.dataloaders import DataLoader
from .by_self import ChannelByIdLoader


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
