from collections import defaultdict
from collections.abc import Sequence

from promise import Promise

from ....checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
)
from ....core.db.connection import allow_writer_in_context
from ....discount import VoucherType
from ....discount.utils.voucher import apply_voucher_to_line
from ...account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ...channel.dataloaders import ChannelByIdLoader
from ...core.dataloaders import DataLoader
from ...discount.dataloaders import (
    CheckoutDiscountByCheckoutIdLoader,
    CheckoutLineDiscountsByCheckoutLineIdLoader,
    VoucherCodeByCodeLoader,
    VoucherInfoByVoucherCodeLoader,
)
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductTypeByVariantIdLoader,
    ProductVariantByIdLoader,
    VariantChannelListingByVariantIdAndChannelIdLoader,
)
from ...shipping.dataloaders import (
    ShippingMethodByIdLoader,
    ShippingMethodChannelListingByChannelSlugLoader,
)
from ...tax.dataloaders import TaxClassByVariantIdLoader, TaxConfigurationByChannelId
from ...warehouse.dataloaders import (
    WarehouseByIdLoader,
)
from .models import CheckoutByTokenLoader, CheckoutLinesByCheckoutTokenLoader
from .promotion_rule_infos import VariantPromotionRuleInfoByCheckoutLineIdLoader


class CheckoutInfoByCheckoutTokenLoader(DataLoader[str, CheckoutInfo]):
    context_key = "checkoutinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout(data):
            checkouts, checkout_line_infos, checkout_discounts, manager = data

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

                voucher_codes = VoucherCodeByCodeLoader(self.context).load_many(
                    {
                        checkout.voucher_code
                        for checkout in checkouts
                        if checkout.voucher_code
                    }
                )

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
                        voucher_codes,
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

                    voucher_code_map = {
                        voucher_code.code: voucher_code
                        for voucher_code in voucher_codes
                        if voucher_code
                    }
                    tax_configuration_by_channel_map = {
                        tax_configuration.channel_id: tax_configuration
                        for tax_configuration in tax_configurations
                    }

                    checkout_info_map = {}
                    for key, checkout, channel, checkout_lines, discounts in zip(
                        keys,
                        checkouts,
                        channels,
                        checkout_line_infos,
                        checkout_discounts,
                    ):
                        shipping_method = shipping_method_map.get(
                            checkout.shipping_method_id
                        )
                        collection_point = collection_points_map.get(
                            checkout.collection_point_id
                        )
                        voucher_code = voucher_code_map.get(checkout.voucher_code)

                        shipping_channel_listings = [
                            listing
                            for channel_listings in listings_for_channels
                            for listing in channel_listings
                            if listing.channel_id == channel.id
                        ]

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
                            tax_configuration=tax_configuration_by_channel_map[
                                channel.id
                            ],
                            discounts=discounts,
                            lines=checkout_lines,
                            manager=manager,
                            shipping_channel_listings=shipping_channel_listings,
                            shipping_method=shipping_method,
                            collection_point=collection_point,
                            voucher=voucher_code.voucher if voucher_code else None,
                            voucher_code=voucher_code,
                            database_connection_name=self.database_connection_name,
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
                        voucher_codes,
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
        discounts = CheckoutDiscountByCheckoutIdLoader(self.context).load_many(keys)
        manager = get_plugin_manager_promise(self.context)
        return Promise.all([checkouts, checkout_line_infos, discounts, manager]).then(
            with_checkout
        )


class CheckoutLinesInfoByCheckoutTokenLoader(
    DataLoader[str, Sequence[CheckoutLineInfo]]
):
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

            @allow_writer_in_context(self.context)
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
                    variant_promotion_rules_info,
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
                rules_info_map = dict(zip(lines_pks, variant_promotion_rules_info))

                lines_info_map = defaultdict(list)
                voucher_infos_map = {
                    voucher_info.voucher_code: voucher_info
                    for voucher_info in voucher_infos
                    if voucher_info is not None and voucher_info.voucher_code
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
                                collections=sorted(
                                    collections_map[line.variant_id],
                                    key=(
                                        lambda collection: (
                                            collection.slug if collection else ""
                                        )
                                    ),
                                ),
                                discounts=checkout_lines_discounts[line.id],
                                tax_class=tax_class_map[line.variant_id],
                                channel=channels[checkout.channel_id],
                                rules_info=rules_info_map[line.id],
                                voucher=None,
                                voucher_code=None,
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
                        apply_voucher_to_line(
                            voucher_info=voucher_info,
                            lines_info=lines_info_map[checkout.pk],
                        )
                return [lines_info_map[key] for key in keys]

            checkout_lines_discounts = CheckoutLineDiscountsByCheckoutLineIdLoader(
                self.context
            ).load_many(lines_pks)
            variant_promotion_rules_info = (
                VariantPromotionRuleInfoByCheckoutLineIdLoader(self.context).load_many(
                    lines_pks
                )
            )
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
                    variant_promotion_rules_info,
                ]
            ).then(with_variants_products_collections)

        checkouts = CheckoutByTokenLoader(self.context).load_many(keys)
        checkout_lines = CheckoutLinesByCheckoutTokenLoader(self.context).load_many(
            keys
        )
        return Promise.all([checkouts, checkout_lines]).then(with_checkout_lines)
