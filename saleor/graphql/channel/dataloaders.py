from ...product.models import ProductChannelListing
from ..core.dataloaders import DataLoader


class ChannelByProductChannelListingIDLoader(DataLoader):
    context_key = "channel_by_product_channel_listing"

    def batch_load(self, keys):
        product_channel_listings = ProductChannelListing.objects.select_related(
            "channel"
        ).in_bulk(keys)
        return [product_channel_listings.get(key).channel for key in keys]
