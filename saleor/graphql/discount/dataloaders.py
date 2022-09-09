from collections import defaultdict

from django.db.models import F

from ...discount import DiscountInfo
from ...discount.interface import VoucherInfo
from ...discount.models import (
    OrderDiscount,
    Sale,
    SaleChannelListing,
    Voucher,
    VoucherChannelListing,
)
from ...discount.utils import (
    fetch_categories,
    fetch_collections,
    fetch_products,
    fetch_sale_channel_listings,
    fetch_variants,
)
from ..core.dataloaders import DataLoader


class DiscountsByDateTimeLoader(DataLoader):
    context_key = "discounts"

    def batch_load(self, keys):
        sales_map = {
            datetime: list(
                Sale.objects.using(self.database_connection_name)
                .active(datetime)
                .order_by("id")
            )
            for datetime in keys
        }
        pks = {s.pk for d, ss in sales_map.items() for s in ss}
        collections = fetch_collections(pks)
        channel_listings = fetch_sale_channel_listings(pks)
        products = fetch_products(pks)
        categories = fetch_categories(pks)
        variants = fetch_variants(pks)

        return [
            [
                DiscountInfo(
                    sale=sale,
                    channel_listings=channel_listings[sale.pk],
                    category_ids=categories[sale.pk],
                    collection_ids=collections[sale.pk],
                    product_ids=products[sale.pk],
                    variants_ids=variants[sale.pk],
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
        sale_channel_listings = (
            SaleChannelListing.objects.using(self.database_connection_name)
            .filter(sale_id__in=sale_ids, channel__slug__in=channel_slugs)
            .annotate(channel_slug=F("channel__slug"))
        )
        sale_channel_listings_by_sale_and_channel_map = {}
        for sale_channel_listing in sale_channel_listings:
            key = (sale_channel_listing.sale_id, sale_channel_listing.channel_slug)
            sale_channel_listings_by_sale_and_channel_map[key] = sale_channel_listing
        return [sale_channel_listings_by_sale_and_channel_map.get(key) for key in keys]


class SaleChannelListingBySaleIdLoader(DataLoader):
    context_key = "salechannelisting_by_sale"

    def batch_load(self, keys):
        sale_channel_listings = SaleChannelListing.objects.using(
            self.database_connection_name
        ).filter(sale_id__in=keys)
        sale_channel_listings_by_sale_map = defaultdict(list)
        for sale_channel_listing in sale_channel_listings:
            sale_channel_listings_by_sale_map[sale_channel_listing.sale_id].append(
                sale_channel_listing
            )
        return [sale_channel_listings_by_sale_map[sale_id] for sale_id in keys]


class VoucherByIdLoader(DataLoader):
    context_key = "voucher_by_id"

    def batch_load(self, keys):
        vouchers = Voucher.objects.using(self.database_connection_name).in_bulk(keys)
        return [vouchers.get(voucher_id) for voucher_id in keys]


class VoucherByCodeLoader(DataLoader):
    context_key = "voucher_by_code"

    def batch_load(self, keys):
        vouchers = (
            Voucher.objects.using(self.database_connection_name)
            .filter(code__in=keys)
            .in_bulk(field_name="code")
        )
        return [vouchers.get(code) for code in keys]


class VoucherChannelListingByVoucherIdAndChanneSlugLoader(DataLoader):
    context_key = "voucherchannelisting_by_voucher_and_channel"

    def batch_load(self, keys):
        voucher_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        voucher_channel_listings = (
            VoucherChannelListing.objects.using(self.database_connection_name)
            .filter(voucher_id__in=voucher_ids, channel__slug__in=channel_slugs)
            .annotate(channel_slug=F("channel__slug"))
        )
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
        voucher_channel_listings = VoucherChannelListing.objects.using(
            self.database_connection_name
        ).filter(voucher_id__in=keys)
        voucher_channel_listings_by_voucher_map = defaultdict(list)
        for voucher_channel_listing in voucher_channel_listings:
            voucher_channel_listings_by_voucher_map[
                voucher_channel_listing.voucher_id
            ].append(voucher_channel_listing)
        return [
            voucher_channel_listings_by_voucher_map[voucher_id] for voucher_id in keys
        ]


class VoucherInfoByVoucherCodeLoader(DataLoader):
    context_key = "voucher_info_by_voucher_code"

    def batch_load(self, keys):
        vouchers_map = (
            Voucher.objects.using(self.database_connection_name)
            # FIXME dataloader should not operate on prefetched data. The channel
            #  listings are used in Voucher's model to calculate a discount amount.
            #  This is a workaround that we should solve by fetching channel_listings
            #  via data loader and passing it to calculate a discount amount.
            .prefetch_related("channel_listings")
            .filter(code__in=keys)
            .in_bulk(field_name="code")
        )
        vouchers = vouchers_map.values()
        voucher_products = (
            Voucher.products.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "product_id")
        )
        voucher_variants = (
            Voucher.variants.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "productvariant_id")
        )
        voucher_collections = (
            Voucher.collections.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "collection_id")
        )
        voucher_categories = (
            Voucher.categories.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "category_id")
        )
        product_pks_map = defaultdict(list)
        variant_pks_map = defaultdict(list)
        category_pks_map = defaultdict(list)
        collection_pks_map = defaultdict(list)
        for voucher_id, product_id in voucher_products:
            product_pks_map[voucher_id].append(product_id)
        for voucher_id, variant_id in voucher_variants:
            variant_pks_map[voucher_id].append(variant_id)
        for voucher_id, category_id in voucher_categories:
            category_pks_map[voucher_id].append(category_id)
        for voucher_id, collection_id in voucher_collections:
            collection_pks_map[voucher_id].append(collection_id)
        voucher_infos = []
        for code in keys:
            voucher = vouchers_map.get(code)
            if not voucher:
                voucher_infos.append(None)
                continue
            voucher_infos.append(
                VoucherInfo(
                    voucher=voucher,
                    product_pks=product_pks_map.get(voucher.id, []),
                    variant_pks=variant_pks_map.get(voucher.id, []),
                    category_pks=category_pks_map.get(voucher.id, []),
                    collection_pks=collection_pks_map.get(voucher.id, []),
                )
            )
        return voucher_infos


class OrderDiscountsByOrderIDLoader(DataLoader):
    context_key = "orderdiscounts_by_order_id"

    def batch_load(self, keys):
        discounts = OrderDiscount.objects.using(self.database_connection_name).filter(
            order_id__in=keys
        )
        discount_map = defaultdict(list)
        for discount in discounts:
            discount_map[discount.order_id].append(discount)
        return [discount_map.get(order_id, []) for order_id in keys]


def load_discounts(request):
    return DiscountsByDateTimeLoader(request).load(request.request_time).get()
