from collections import defaultdict

from django.db.models import F

from ...discount import DiscountInfo
from ...discount.models import Sale, SaleChannelListing, Voucher, VoucherChannelListing
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


class SaleChannelListingBySaleIdAndChanneSlugLoader(DataLoader):
    context_key = "salechannelisting_by_sale_and_channel"

    def batch_load(self, keys):
        sale_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        sale_channel_listings = SaleChannelListing.objects.filter(
            sale_id__in=sale_ids, channel__slug__in=channel_slugs
        ).annotate(channel_slug=F("channel__slug"))
        sale_channel_listings_by_sale_and_channel_map = {}
        for sale_channel_listing in sale_channel_listings:
            key = (sale_channel_listing.sale_id, sale_channel_listing.channel_slug)
            sale_channel_listings_by_sale_and_channel_map[key] = sale_channel_listing
        return [sale_channel_listings_by_sale_and_channel_map.get(key) for key in keys]


class SaleChannelListingBySaleIdLoader(DataLoader):
    context_key = "salechannelisting_by_sale"

    def batch_load(self, keys):
        sale_channel_listings = SaleChannelListing.objects.filter(sale_id__in=keys)
        sale_channel_listings_by_sale_map = defaultdict(list)
        for sale_channel_listing in sale_channel_listings:
            sale_channel_listings_by_sale_map[sale_channel_listing.sale_id].append(
                sale_channel_listing
            )
        return [sale_channel_listings_by_sale_map[sale_id] for sale_id in keys]


class VoucherByIdLoader(DataLoader):
    context_key = "voucher_by_id"

    def batch_load(self, keys):
        vouchers = Voucher.objects.in_bulk(keys)
        return [vouchers.get(voucher_id) for voucher_id in keys]


class VoucherChannelListingByVoucherIdAndChanneSlugLoader(DataLoader):
    context_key = "voucherchannelisting_by_voucher_and_channel"

    def batch_load(self, keys):
        voucher_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        voucher_channel_listings = VoucherChannelListing.objects.filter(
            voucher_id__in=voucher_ids, channel__slug__in=channel_slugs
        ).annotate(channel_slug=F("channel__slug"))
        voucher_channel_listings_by_voucher_and_channel_map = {}
        for voucher_channel_listing in voucher_channel_listings:
            key = (
                voucher_channel_listing.voucher_id,
                voucher_channel_listing.channel_slug,
            )
            voucher_channel_listings_by_voucher_and_channel_map[
                key
            ] = voucher_channel_listing
        return [
            voucher_channel_listings_by_voucher_and_channel_map.get(key) for key in keys
        ]


class VoucherChannelListingByVoucherIdLoader(DataLoader):
    context_key = "voucherchannellisting_by_voucher"

    def batch_load(self, keys):
        voucher_channel_listings = VoucherChannelListing.objects.filter(
            voucher_id__in=keys
        )
        voucher_channel_listings_by_voucher_map = defaultdict(list)
        for voucher_channel_listing in voucher_channel_listings:
            voucher_channel_listings_by_voucher_map[
                voucher_channel_listing.voucher_id
            ].append(voucher_channel_listing)
        return [
            voucher_channel_listings_by_voucher_map[voucher_id] for voucher_id in keys
        ]
