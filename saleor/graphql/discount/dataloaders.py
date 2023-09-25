from collections import defaultdict
from typing import List, Optional

from django.db.models import F, Max, Sum

from ...discount import DiscountInfo
from ...discount.interface import VoucherInfo
from ...discount.models import (
    CheckoutLineDiscount,
    OrderDiscount,
    Sale,
    SaleChannelListing,
    Voucher,
    VoucherChannelListing,
    VoucherCode,
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
        collections = fetch_collections(
            pks, database_connection_name=self.database_connection_name
        )
        channel_listings = fetch_sale_channel_listings(
            pks, self.database_connection_name
        )
        products = fetch_products(
            pks, database_connection_name=self.database_connection_name
        )
        categories = fetch_categories(
            pks, database_connection_name=self.database_connection_name
        )
        variants = fetch_variants(
            pks, database_connection_name=self.database_connection_name
        )

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


class VoucherCodeByCodeLoader(DataLoader):
    context_key = "voucher_code_by_code"

    def batch_load(self, keys):
        voucher_codes = (
            VoucherCode.objects.using(self.database_connection_name)
            .select_related("voucher")
            .filter(code__in=keys)
        )
        voucher_map = {
            voucher_code.code: voucher_code for voucher_code in voucher_codes
        }
        return [voucher_map.get(code) for code in keys]


class CodeByVoucherIDLoader(DataLoader):
    """Fetch voucher code.

    This dataloader will be deprecated together with `code` field.
    """

    context_key = "voucher_code"

    def batch_load(self, keys):
        voucher_codes = VoucherCode.objects.using(self.database_connection_name).filter(
            voucher_id__in=keys
        )
        voucher_codes_map = {}
        for voucher_code in voucher_codes:
            voucher_codes_map[voucher_code.voucher_id] = voucher_code.code
        return [voucher_codes_map.get(voucher_id) for voucher_id in keys]


class UsedByVoucherIDLoader(DataLoader):
    """Fetch voucher used.

    This dataloader will be deprecated together with `used` field.
    """

    context_key = "voucher_used"

    def batch_load(self, keys):
        vouchers = (
            Voucher.objects.using(self.database_connection_name)
            .filter(id__in=keys)
            .annotate(max_used=Sum("codes__used"))
        )
        vouchers_map = {}
        for voucher in vouchers:
            vouchers_map[voucher.id] = voucher.max_used  # type: ignore
        return [vouchers_map.get(voucher_id) for voucher_id in keys]


class UsageLimitByVoucherIDLoader(DataLoader):
    """Fetch voucher usage limit.

    This dataloader will be deprecated together with `usage_limit` field.
    """

    context_key = "voucher_usage_limit"

    def batch_load(self, keys):
        vouchers = (
            Voucher.objects.using(self.database_connection_name)
            .filter(id__in=keys)
            .annotate(max_used_limit=Max("codes__usage_limit"))
        )
        vouchers_map = {}
        for voucher in vouchers:
            vouchers_map[voucher.id] = voucher.max_used_limit  # type: ignore
        return [vouchers_map.get(voucher_id) for voucher_id in keys]


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


class VoucherInfoByVoucherCodeLoader(DataLoader[str, Optional[VoucherInfo]]):
    context_key = "voucher_info_by_voucher_code"

    def batch_load(self, keys):
        # FIXME dataloader should not operate on prefetched data. The channel
        #  listings are used in Voucher's model to calculate a discount amount.
        #  This is a workaround that we should solve by fetching channel_listings
        #  via data loader and passing it to calculate a discount amount.
        voucher_codes_map = (
            VoucherCode.objects.using(self.database_connection_name)
            .prefetch_related("voucher__channel_listings")
            .filter(code__in=keys)
            .in_bulk(field_name="code")
        )

        vouchers = set([code.voucher for code in voucher_codes_map.values()])
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
        voucher_infos: List[Optional[VoucherInfo]] = []

        for code in keys:
            voucher_code = voucher_codes_map.get(code)
            if not voucher_code:
                voucher_infos.append(None)
                continue
            voucher_infos.append(
                VoucherInfo(
                    voucher=voucher_code.voucher,
                    product_pks=product_pks_map.get(voucher_code.voucher_id, []),
                    variant_pks=variant_pks_map.get(voucher_code.voucher_id, []),
                    category_pks=category_pks_map.get(voucher_code.voucher_id, []),
                    collection_pks=collection_pks_map.get(voucher_code.voucher_id, []),
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


class CheckoutLineDiscountsByCheckoutLineIdLoader(DataLoader):
    context_key = "checkout_line_discounts_by_checkout_line_id"

    def batch_load(self, keys):
        discounts = CheckoutLineDiscount.objects.using(
            self.database_connection_name
        ).filter(line_id__in=keys)
        discount_map = defaultdict(list)
        for discount in discounts:
            discount_map[discount.line_id].append(discount)
        return [discount_map.get(checkout_line_id, []) for checkout_line_id in keys]
