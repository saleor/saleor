from collections import defaultdict
from typing import Iterable, List, Tuple

from django.db.models import F
from promise import Promise

from ...checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    apply_voucher_to_checkout_line,
    get_delivery_method_info,
    update_delivery_method_lists_for_checkout_info,
)
from ...checkout.models import Checkout, CheckoutLine, CheckoutMetadata
from ...checkout.problems import (
    CHANNEL_SLUG,
    CHECKOUT_LINE_PROBLEM_TYPE,
    CHECKOUT_PROBLEM_TYPE,
    COUNTRY_CODE,
    PRODUCT_ID,
    VARIANT_ID,
    get_checkout_lines_problems,
    get_checkout_problems,
)
from ...discount import VoucherType
from ...payment.models import TransactionItem
from ...product.models import ProductChannelListing
from ...warehouse.models import Stock
from ..account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ..channel.dataloaders import ChannelByIdLoader
from ..core.dataloaders import DataLoader
from ..discount.dataloaders import (
    CheckoutLineDiscountsByCheckoutLineIdLoader,
    VoucherByCodeLoader,
    VoucherInfoByVoucherCodeLoader,
)
from ..plugins.dataloaders import get_plugin_manager_promise
from ..product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductChannelListingByProductIdAndChannelSlugLoader,
    ProductTypeByVariantIdLoader,
    ProductVariantByIdLoader,
    VariantChannelListingByVariantIdAndChannelIdLoader,
)
from ..shipping.dataloaders import (
    ShippingMethodByIdLoader,
    ShippingMethodChannelListingByChannelSlugLoader,
)
from ..tax.dataloaders import TaxClassByVariantIdLoader, TaxConfigurationByChannelId
from ..warehouse.dataloaders import (
    StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader,
    WarehouseByIdLoader,
)


class CheckoutByTokenLoader(DataLoader[str, Checkout]):
    context_key = "checkout_by_token"

    def batch_load(self, keys):
        checkouts = Checkout.objects.using(self.database_connection_name).in_bulk(keys)
        return [checkouts.get(token) for token in keys]


class CheckoutLinesInfoByCheckoutTokenLoader(DataLoader[str, List[CheckoutLineInfo]]):
    context_key = "checkoutlinesinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout_lines(results):
            checkouts, checkout_lines = results

            variants_pks = set()
            lines_pks = set()
            for lines in checkout_lines:
                for line in lines:
                    lines_pks.add(line.id)
                    variants_pks.add(line.variant_id)
            lines_pks = list(lines_pks)
            variants_pks = list(variants_pks)
            if not variants_pks:
                return [[] for _ in keys]

            channel_pks = [checkout.channel_id for checkout in checkouts]

            def with_variants_products_collections(results):
                (
                    variants,
                    products,
                    product_types,
                    collections,
                    tax_classes,
                    channel_listings,
                    voucher_infos,
                    channels,
                    checkout_lines_discounts,
                ) = results
                variants_map = dict(zip(variants_pks, variants))
                products_map = dict(zip(variants_pks, products))
                product_types_map = dict(zip(variants_pks, product_types))
                collections_map = dict(zip(variants_pks, collections))
                tax_class_map = dict(zip(variants_pks, tax_classes))
                channel_listings_map = dict(
                    zip(variant_ids_channel_ids, channel_listings)
                )
                channels = dict(zip(channel_pks, channels))
                checkout_lines_discounts = dict(
                    zip(lines_pks, checkout_lines_discounts)
                )

                lines_info_map = defaultdict(list)
                voucher_infos_map = {
                    voucher_info.voucher.code: voucher_info
                    for voucher_info in voucher_infos
                    if voucher_info
                }
                for checkout, lines in zip(checkouts, checkout_lines):
                    lines_info_map[checkout.pk].extend(
                        [
                            CheckoutLineInfo(
                                line=line,
                                variant=variants_map[line.variant_id],
                                channel_listing=channel_listings_map[
                                    (line.variant_id, checkout.channel_id)
                                ],
                                product=products_map[line.variant_id],
                                product_type=product_types_map[line.variant_id],
                                collections=collections_map[line.variant_id],
                                discounts=checkout_lines_discounts[line.id],
                                tax_class=tax_class_map[line.variant_id],
                                channel=channels[checkout.channel_id],
                            )
                            for line in lines
                        ]
                    )

                for checkout in checkouts:
                    if not checkout.voucher_code:
                        continue
                    voucher_info = voucher_infos_map.get(checkout.voucher_code)
                    if not voucher_info:
                        continue
                    voucher = voucher_info.voucher
                    if (
                        voucher.type == VoucherType.SPECIFIC_PRODUCT
                        or voucher.apply_once_per_order
                    ):
                        apply_voucher_to_checkout_line(
                            voucher_info=voucher_info,
                            checkout=checkout,
                            lines_info=lines_info_map[checkout.pk],
                        )
                return [lines_info_map[key] for key in keys]

            checkout_lines_discounts = CheckoutLineDiscountsByCheckoutLineIdLoader(
                self.context
            ).load_many(lines_pks)
            variants = ProductVariantByIdLoader(self.context).load_many(variants_pks)
            products = ProductByVariantIdLoader(self.context).load_many(variants_pks)
            product_types = ProductTypeByVariantIdLoader(self.context).load_many(
                variants_pks
            )
            collections = CollectionsByVariantIdLoader(self.context).load_many(
                variants_pks
            )
            tax_classes = TaxClassByVariantIdLoader(self.context).load_many(
                variants_pks
            )

            voucher_codes = {
                checkout.voucher_code for checkout in checkouts if checkout.voucher_code
            }
            voucher_infos = VoucherInfoByVoucherCodeLoader(self.context).load_many(
                voucher_codes
            )

            variant_ids_channel_ids = []
            for channel_id, lines in zip(channel_pks, checkout_lines):
                variant_ids_channel_ids.extend(
                    [(line.variant_id, channel_id) for line in lines]
                )

            channel_listings = VariantChannelListingByVariantIdAndChannelIdLoader(
                self.context
            ).load_many(variant_ids_channel_ids)

            channels = ChannelByIdLoader(self.context).load_many(channel_pks)
            return Promise.all(
                [
                    variants,
                    products,
                    product_types,
                    collections,
                    tax_classes,
                    channel_listings,
                    voucher_infos,
                    channels,
                    checkout_lines_discounts,
                ]
            ).then(with_variants_products_collections)

        checkouts = CheckoutByTokenLoader(self.context).load_many(keys)
        checkout_lines = CheckoutLinesByCheckoutTokenLoader(self.context).load_many(
            keys
        )
        return Promise.all([checkouts, checkout_lines]).then(with_checkout_lines)


class CheckoutByUserLoader(DataLoader[int, List[Checkout]]):
    context_key = "checkout_by_user"

    def batch_load(self, keys):
        checkouts = Checkout.objects.using(self.database_connection_name).filter(
            user_id__in=keys, channel__is_active=True
        )
        checkout_by_user_map = defaultdict(list)
        for checkout in checkouts:
            checkout_by_user_map[checkout.user_id].append(checkout)
        return [checkout_by_user_map[user_id] for user_id in keys]


class CheckoutByUserAndChannelLoader(DataLoader[Tuple[int, str], List[Checkout]]):
    context_key = "checkout_by_user_and_channel"

    def batch_load(self, keys: Iterable[Tuple[int, str]]):
        user_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        checkouts = (
            Checkout.objects.using(self.database_connection_name)
            .filter(
                user_id__in=user_ids,
                channel__slug__in=channel_slugs,
                channel__is_active=True,
            )
            .annotate(channel_slug=F("channel__slug"))
        )
        checkout_by_user_and_channel_map = defaultdict(list)
        for checkout in checkouts:
            key = (checkout.user_id, checkout.channel_slug)
            checkout_by_user_and_channel_map[key].append(checkout)
        return [checkout_by_user_and_channel_map[key] for key in keys]


class CheckoutInfoByCheckoutTokenLoader(DataLoader[str, CheckoutInfo]):
    context_key = "checkoutinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout(data):
            checkouts, checkout_line_infos, manager = data
            from ..channel.dataloaders import ChannelByIdLoader

            channel_pks = [checkout.channel_id for checkout in checkouts]

            def with_channel(channels):
                billing_address_ids = {
                    checkout.billing_address_id
                    for checkout in checkouts
                    if checkout.billing_address_id
                }
                shipping_address_ids = {
                    checkout.shipping_address_id
                    for checkout in checkouts
                    if checkout.shipping_address_id
                }
                addresses = AddressByIdLoader(self.context).load_many(
                    billing_address_ids | shipping_address_ids
                )
                users = UserByUserIdLoader(self.context).load_many(
                    [checkout.user_id for checkout in checkouts if checkout.user_id]
                )
                shipping_method_ids = [
                    checkout.shipping_method_id
                    for checkout in checkouts
                    if checkout.shipping_method_id
                ]
                shipping_methods = ShippingMethodByIdLoader(self.context).load_many(
                    shipping_method_ids
                )
                channel_slugs = [channel.slug for channel in channels]
                shipping_method_channel_listings = (
                    ShippingMethodChannelListingByChannelSlugLoader(
                        self.context
                    ).load_many(channel_slugs)
                )
                collection_point_ids = [
                    checkout.collection_point_id
                    for checkout in checkouts
                    if checkout.collection_point_id
                ]
                collection_points = WarehouseByIdLoader(self.context).load_many(
                    collection_point_ids
                )
                voucher_codes = {
                    checkout.voucher_code
                    for checkout in checkouts
                    if checkout.voucher_code
                }
                vouchers = VoucherByCodeLoader(self.context).load_many(voucher_codes)
                channel_ids = [channel.id for channel in channels]
                tax_configurations = TaxConfigurationByChannelId(
                    self.context
                ).load_many(channel_ids)

                def with_checkout_info(results):
                    (
                        addresses,
                        users,
                        shipping_methods,
                        listings_for_channels,
                        collection_points,
                        vouchers,
                        tax_configurations,
                    ) = results
                    address_map = {address.id: address for address in addresses}
                    user_map = {user.id: user for user in users}
                    shipping_method_map = {
                        shipping_method.id: shipping_method
                        for shipping_method in shipping_methods
                    }
                    collection_points_map = {
                        collection_point.id: collection_point
                        for collection_point in collection_points
                    }
                    voucher_map = {voucher.code: voucher for voucher in vouchers}
                    tax_configuration_by_channel_map = {
                        tax_configuration.channel_id: tax_configuration
                        for tax_configuration in tax_configurations
                    }

                    checkout_info_map = {}
                    for key, checkout, channel, checkout_lines in zip(
                        keys, checkouts, channels, checkout_line_infos
                    ):
                        shipping_method = shipping_method_map.get(
                            checkout.shipping_method_id
                        )
                        collection_point = collection_points_map.get(
                            checkout.collection_point_id
                        )
                        shipping_address = address_map.get(checkout.shipping_address_id)
                        delivery_method_info = get_delivery_method_info(
                            None, shipping_address
                        )
                        voucher = voucher_map.get(checkout.voucher_code)
                        checkout_info = CheckoutInfo(
                            checkout=checkout,
                            user=user_map.get(checkout.user_id),
                            channel=channel,
                            billing_address=address_map.get(
                                checkout.billing_address_id
                            ),
                            shipping_address=address_map.get(
                                checkout.shipping_address_id
                            ),
                            delivery_method_info=delivery_method_info,
                            tax_configuration=tax_configuration_by_channel_map[
                                channel.id
                            ],
                            valid_pick_up_points=[],
                            all_shipping_methods=[],
                            voucher=voucher,
                        )
                        shipping_method_listings = [
                            listing
                            for channel_listings in listings_for_channels
                            for listing in channel_listings
                            if listing.channel_id == channel.id
                        ]
                        update_delivery_method_lists_for_checkout_info(
                            checkout_info,
                            shipping_method,
                            collection_point,
                            shipping_address,
                            checkout_lines,
                            manager,
                            shipping_method_listings,
                        )
                        checkout_info_map[key] = checkout_info

                    return [checkout_info_map[key] for key in keys]

                return Promise.all(
                    [
                        addresses,
                        users,
                        shipping_methods,
                        shipping_method_channel_listings,
                        collection_points,
                        vouchers,
                        tax_configurations,
                    ]
                ).then(with_checkout_info)

            return (
                ChannelByIdLoader(self.context)
                .load_many(channel_pks)
                .then(with_channel)
            )

        checkouts = CheckoutByTokenLoader(self.context).load_many(keys)
        checkout_line_infos = CheckoutLinesInfoByCheckoutTokenLoader(
            self.context
        ).load_many(keys)
        manager = get_plugin_manager_promise(self.context)
        return Promise.all([checkouts, checkout_line_infos, manager]).then(
            with_checkout
        )


class CheckoutLineByIdLoader(DataLoader[str, CheckoutLine]):
    context_key = "checkout_line_by_id"

    def batch_load(self, keys):
        checkout_lines = CheckoutLine.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [checkout_lines.get(line_id) for line_id in keys]


class CheckoutLinesByCheckoutTokenLoader(DataLoader[str, List[CheckoutLine]]):
    context_key = "checkoutlines_by_checkout"

    def batch_load(self, keys):
        lines = CheckoutLine.objects.using(self.database_connection_name).filter(
            checkout_id__in=keys
        )
        line_map = defaultdict(list)
        for line in lines.iterator():
            line_map[line.checkout_id].append(line)
        return [line_map.get(checkout_id, []) for checkout_id in keys]


class TransactionItemsByCheckoutIDLoader(DataLoader[str, List[TransactionItem]]):
    context_key = "transaction_items_by_checkout_id"

    def batch_load(self, keys):
        transactions = (
            TransactionItem.objects.using(self.database_connection_name)
            .filter(checkout_id__in=keys)
            .order_by("pk")
        )
        transactions_map = defaultdict(list)
        for transaction in transactions:
            transactions_map[transaction.checkout_id].append(transaction)
        return [transactions_map[checkout_id] for checkout_id in keys]


class CheckoutMetadataByCheckoutIdLoader(DataLoader[str, CheckoutMetadata]):
    context_key = "checkout_metadata_by_checkout_id"

    def batch_load(self, keys):
        checkout_metadata = CheckoutMetadata.objects.using(
            self.database_connection_name
        ).in_bulk(keys, field_name="checkout_id")
        return [checkout_metadata.get(checkout_id) for checkout_id in keys]


class ChannelByCheckoutLineIDLoader(DataLoader):
    context_key = "channel_by_checkout_line"

    def batch_load(self, keys):
        def channel_by_lines(checkout_lines):
            checkout_ids = [line.checkout_id for line in checkout_lines]

            def channels_by_checkout(checkouts):
                channel_ids = [checkout.channel_id for checkout in checkouts]

                return ChannelByIdLoader(self.context).load_many(channel_ids)

            return (
                CheckoutByTokenLoader(self.context)
                .load_many(checkout_ids)
                .then(channels_by_checkout)
            )

        return (
            CheckoutLineByIdLoader(self.context).load_many(keys).then(channel_by_lines)
        )


class CheckoutLinesProblemsByCheckoutIdLoader(
    DataLoader[str, dict[str, list[CHECKOUT_LINE_PROBLEM_TYPE]]]
):
    context_key = "checkout_lines_problems_by_checkout_id"

    def batch_load(self, keys):
        stock_dataloader = (
            StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
                self.context
            )
        )

        def _resolve_problems(data):
            checkout_infos, checkout_lines = data
            variant_data_set: set[
                tuple[
                    VARIANT_ID,
                    CHANNEL_SLUG,
                    COUNTRY_CODE,
                ]
            ] = set()
            product_data_set: set[
                tuple[
                    PRODUCT_ID,
                    CHANNEL_SLUG,
                ]
            ] = set()
            checkout_infos_map = {
                checkout_info.checkout.pk: checkout_info
                for checkout_info in checkout_infos
            }
            for lines in checkout_lines:
                for line in lines:
                    variant_data_set.add(
                        (
                            line.variant.id,
                            line.channel.slug,
                            checkout_infos_map[line.line.checkout_id].checkout.country,
                        )
                    )
                    product_data_set.add(
                        (
                            line.product.id,
                            line.channel.slug,
                        )
                    )
            variant_data_list = list(variant_data_set)
            product_data_list = list(product_data_set)

            def _prepare_problems(data):
                (
                    variant_stocks,
                    product_channel_listings,
                ) = data
                variant_stock_map: dict[
                    tuple[
                        VARIANT_ID,
                        CHANNEL_SLUG,
                        COUNTRY_CODE,
                    ],
                    Iterable[Stock],
                ] = dict(zip(variant_data_list, variant_stocks))
                product_channel_listings_map: dict[
                    tuple[
                        PRODUCT_ID,
                        CHANNEL_SLUG,
                    ],
                    ProductChannelListing,
                ] = dict(zip(product_data_set, product_channel_listings))

                problems = {}

                for checkout_info, lines in zip(checkout_infos, checkout_lines):
                    checkout_id = checkout_info.checkout.pk
                    problems[checkout_id] = get_checkout_lines_problems(
                        checkout_info,
                        lines,
                        variant_stock_map,
                        product_channel_listings_map,
                    )
                return [problems.get(key, []) for key in keys]

            variant_stocks = stock_dataloader.load_many(
                [
                    (variant_id, country_code, channel_slug)
                    for variant_id, channel_slug, country_code in variant_data_list
                ]
            )
            product_channel_listings = (
                ProductChannelListingByProductIdAndChannelSlugLoader(
                    self.context
                ).load_many(
                    [
                        (
                            product_id,
                            channel_slug,
                        )
                        for product_id, channel_slug in product_data_list
                    ]
                )
            )

            return Promise.all([variant_stocks, product_channel_listings]).then(
                _prepare_problems
            )

        checkout_infos = CheckoutInfoByCheckoutTokenLoader(self.context).load_many(keys)
        lines = CheckoutLinesInfoByCheckoutTokenLoader(self.context).load_many(keys)
        return Promise.all([checkout_infos, lines]).then(_resolve_problems)


class CheckoutProblemsByCheckoutIdDataloader(
    DataLoader[str, dict[str, list[CHECKOUT_PROBLEM_TYPE]]]
):
    context_key = "checkout_problems_by_checkout_id"

    def batch_load(self, keys):
        line_problems_dataloader = CheckoutLinesProblemsByCheckoutIdLoader(self.context)

        def _resolve_problems(
            checkouts_lines_problems: list[dict[str, list[CHECKOUT_LINE_PROBLEM_TYPE]]]
        ):
            checkout_problems = defaultdict(list)
            for checkout_pk, checkout_lines_problems in zip(
                keys, checkouts_lines_problems
            ):
                checkout_problems[checkout_pk] = get_checkout_problems(
                    checkout_lines_problems
                )

            return [checkout_problems.get(key, []) for key in keys]

        return line_problems_dataloader.load_many(keys).then(_resolve_problems)
