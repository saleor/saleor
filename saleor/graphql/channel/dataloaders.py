from ...channel.models import Channel
from ..checkout.dataloaders import CheckoutByIdLoader, CheckoutLineByIdLoader
from ..core.dataloaders import DataLoader
from ..product.dataloaders import (
    CollectionChannelListingByIdLoader,
    ProductChannelListingByIdLoader,
    ProductVariantChannelListingByIdLoader,
)


class ChannelByIdLoader(DataLoader):
    context_key = "channel_by_id"

    def batch_load(self, keys):
        channels = Channel.objects.in_bulk(keys)
        return [channels.get(channel_id) for channel_id in keys]


class ChannelByProductChannelListingIDLoader(DataLoader):
    context_key = "channel_by_product_channel_listing"

    def batch_load(self, keys):
        def channel_by_product_channel_listings(product_channel_listings):
            channel_ids = [
                product_channel_listing.channel_id
                for product_channel_listing in product_channel_listings
            ]
            return ChannelByIdLoader(self.context).load_many(channel_ids)

        return (
            ProductChannelListingByIdLoader(self.context)
            .load_many(keys)
            .then(channel_by_product_channel_listings)
        )


class ChannelByProductVariantChannelListingIDLoader(DataLoader):
    context_key = "channel_by_product_variant_channel_listing"

    def batch_load(self, keys):
        def channel_by_variant_channel_listing(variant_channel_listings):
            channel_ids = [
                variant_channel_listing.channel_id
                for variant_channel_listing in variant_channel_listings
            ]
            return ChannelByIdLoader(self.context).load_many(channel_ids)

        return (
            ProductVariantChannelListingByIdLoader(self.context)
            .load_many(keys)
            .then(channel_by_variant_channel_listing)
        )


class ChannelByCollectionChannelListingIDLoader(DataLoader):
    context_key = "channel_by_collection_channel_listing"

    def batch_load(self, keys):
        def channel_by_collection_channel_listing(collection_channel_listings):
            channel_ids = [
                collection_channel_listing.channel_id
                for collection_channel_listing in collection_channel_listings
            ]
            return ChannelByIdLoader(self.context).load_many(channel_ids)

        return (
            CollectionChannelListingByIdLoader(self.context)
            .load_many(keys)
            .then(channel_by_collection_channel_listing)
        )


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
