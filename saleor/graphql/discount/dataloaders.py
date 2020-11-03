from django.db.models import F

from ...discount import DiscountInfo
from ...discount.models import Sale, SaleChannelListing, Voucher
from ...discount.utils import (
    fetch_categories,
    fetch_collections,
    fetch_products,
    fetch_sale_channel_listings,
)
from ..core.dataloaders import DataLoader


class DiscountsByDateTimeLoader(DataLoader):
    context_key = "discounts"

    def batch_load(self, keys):
        sales_map = {
            datetime: list(Sale.objects.active(datetime).order_by("id"))
            for datetime in keys
        }
        pks = {s.pk for d, ss in sales_map.items() for s in ss}
        collections = fetch_collections(pks)
        channel_listings = fetch_sale_channel_listings(pks)
        products = fetch_products(pks)
        categories = fetch_categories(pks)

        return [
            [
                DiscountInfo(
                    sale=sale,
                    channel_listings=channel_listings[sale.pk],
                    category_ids=categories[sale.pk],
                    collection_ids=collections[sale.pk],
                    product_ids=products[sale.pk],
                )
                for sale in sales_map[datetime]
            ]
            for datetime in keys
        ]


class VoucherByIdLoader(DataLoader):
    context_key = "voucher_by_id"

    def batch_load(self, keys):
        vouchers = Voucher.objects.in_bulk(keys)
        return [vouchers.get(voucher_id) for voucher_id in keys]


class SaleChannelListingBySaleIdAndChanneSlugLoader(DataLoader):
    context_key = "salechannelisting_by_sale_and_channel"

    def batch_load(self, keys):
        sale_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        sales_channel_listings = SaleChannelListing.objects.filter(
            sale_id__in=sale_ids, channel__slug__in=channel_slugs
        ).annotate(channel_slug=F("channel__slug"))
        sales_channel_listings_by_sale_and_channel_map = {}
        for sales_channel_listing in sales_channel_listings:
            key = (sales_channel_listing.sale_id, sales_channel_listing.channel_slug)
            sales_channel_listings_by_sale_and_channel_map[key] = sales_channel_listing
        return [sales_channel_listings_by_sale_and_channel_map[key] for key in keys]
