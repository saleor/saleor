from ...channel.models import Channel
from ...product.models import ProductChannelListing
from ..checkout.dataloaders import CheckoutByIdLoader, CheckoutLineByIdLoader
from ..core.dataloaders import DataLoader


class ChannelByIdLoader(DataLoader):
    context_key = "channel_by_id"

    def batch_load(self, keys):
        channels = Channel.objects.in_bulk(keys)
        return [channels.get(channel_id) for channel_id in keys]


class ChannelByProductChannelListingIDLoader(DataLoader):
    context_key = "channel_by_product_channel_listing"

    def batch_load(self, keys):
        # TODO: Remove this before merge to master.
        # Avoid use `select_related` in dataloaders. We should use similar solution
        # like `ChannelByCheckoutLineIDLoader`
        product_channel_listings = ProductChannelListing.objects.select_related(
            "channel"
        ).in_bulk(keys)
        return [product_channel_listings.get(key).channel for key in keys]


class ChannelByCheckoutLineIDLoader(DataLoader):
    context_key = "channel_by_checkout_line"

    def batch_load(self, keys):
        def channel_by_lines(checkout_lines):
            line_id_checkout_id_map = {
                line.id: line.checkout_id for line in checkout_lines
            }

            def channels_by_checkout(checkouts):
                checkout_id_chanel_id_map = {
                    checkout.pk: checkout.channel_id for checkout in checkouts
                }

                return ChannelByIdLoader(self.context).load_many(
                    list(checkout_id_chanel_id_map.values())
                )

            return (
                CheckoutByIdLoader(self.context)
                .load_many(list(line_id_checkout_id_map.values()))
                .then(channels_by_checkout)
            )

        return (
            CheckoutLineByIdLoader(self.context).load_many(keys).then(channel_by_lines)
        )
