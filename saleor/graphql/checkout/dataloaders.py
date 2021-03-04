from collections import defaultdict

from django.db.models import F
from promise import Promise

from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ...checkout.models import Checkout, CheckoutLine
from ..account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ..core.dataloaders import DataLoader
from ..product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductVariantByIdLoader,
    VariantChannelListingByVariantIdAndChannelIdLoader,
)
from ..shipping.dataloaders import (
    ShippingMethodByIdLoader,
    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader,
)


class CheckoutByTokenLoader(DataLoader):
    context_key = "checkout_by_token"

    def batch_load(self, keys):
        checkouts = Checkout.objects.filter(token__in=keys).in_bulk()
        return [checkouts[token] for token in keys]


class CheckoutLinesInfoByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlinesinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout_lines(results):
            checkouts, checkout_lines = results
            variants_pks = list(
                {line.variant_id for lines in checkout_lines for line in lines}
            )
            if not variants_pks:
                return [[] for _ in keys]

            channel_pks = [checkout.channel_id for checkout in checkouts]

            def with_variants_products_collections(results):
                variants, products, collections, channel_listings = results
                variants_map = dict(zip(variants_pks, variants))
                products_map = dict(zip(variants_pks, products))
                collections_map = dict(zip(variants_pks, collections))
                channel_listings_map = dict(
                    zip(variant_ids_channel_ids, channel_listings)
                )

                lines_info_map = defaultdict(list)
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
                                collections=collections_map[line.variant_id],
                            )
                            for line in lines
                        ]
                    )
                return [lines_info_map[key] for key in keys]

            variants = ProductVariantByIdLoader(self.context).load_many(variants_pks)
            products = ProductByVariantIdLoader(self.context).load_many(variants_pks)
            collections = CollectionsByVariantIdLoader(self.context).load_many(
                variants_pks
            )

            variant_ids_channel_ids = []
            for channel_id, lines in zip(channel_pks, checkout_lines):
                variant_ids_channel_ids.extend(
                    [(line.variant_id, channel_id) for line in lines]
                )

            channel_listings = VariantChannelListingByVariantIdAndChannelIdLoader(
                self.context
            ).load_many(variant_ids_channel_ids)
            return Promise.all(
                [variants, products, collections, channel_listings]
            ).then(with_variants_products_collections)

        checkouts = CheckoutByTokenLoader(self.context).load_many(keys)
        checkout_lines = CheckoutLinesByCheckoutTokenLoader(self.context).load_many(
            keys
        )
        return Promise.all([checkouts, checkout_lines]).then(with_checkout_lines)


class CheckoutByIdLoader(DataLoader):
    context_key = "checkout_by_id"

    def batch_load(self, keys):
        checkouts = Checkout.objects.in_bulk(keys)
        return [checkouts.get(checkout_id) for checkout_id in keys]


class CheckoutByUserLoader(DataLoader):
    context_key = "checkout_by_user"

    def batch_load(self, keys):
        checkouts = Checkout.objects.filter(user_id__in=keys, channel__is_active=True)
        checkout_by_user_map = defaultdict(list)
        for checkout in checkouts:
            checkout_by_user_map[checkout.user_id].append(checkout)
        return [checkout_by_user_map.get(user_id) for user_id in keys]


class CheckoutByUserAndChannelLoader(DataLoader):
    context_key = "checkout_by_user_and_channel"

    def batch_load(self, keys):
        user_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        checkouts = Checkout.objects.filter(
            user_id__in=user_ids,
            channel__slug__in=channel_slugs,
            channel__is_active=True,
        ).annotate(channel_slug=F("channel__slug"))
        checkout_by_user_and_channel_map = defaultdict(list)
        for checkout in checkouts:
            key = (checkout.user_id, checkout.channel_slug)
            checkout_by_user_and_channel_map[key].append(checkout)
        return [checkout_by_user_and_channel_map.get(key) for key in keys]


class CheckoutInfoByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout(checkouts):
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
                shipping_method_ids_channel_slugs = [
                    (checkout.shipping_method_id, channel.slug)
                    for checkout, channel in zip(checkouts, channels)
                    if checkout.shipping_method_id
                ]
                shipping_method_channel_listings = (
                    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(
                        self.context
                    ).load_many(shipping_method_ids_channel_slugs)
                )

                def with_checkout_info(results):
                    (
                        addresses,
                        users,
                        shipping_methods,
                        channel_listings,
                    ) = results
                    address_map = {address.id: address for address in addresses}
                    user_map = {user.id: user for user in users}
                    shipping_method_map = {
                        shipping_method.id: shipping_method
                        for shipping_method in shipping_methods
                    }
                    shipping_method_channel_listing_map = {
                        (listing.shipping_method_id, listing.channel_id): listing
                        for listing in channel_listings
                    }

                    checkout_info_map = {}
                    for key, checkout, channel in zip(keys, checkouts, channels):
                        checkout_info_map[key] = CheckoutInfo(
                            checkout=checkout,
                            user=user_map.get(checkout.user_id),
                            channel=channel,
                            billing_address=address_map.get(
                                checkout.billing_address_id
                            ),
                            shipping_address=address_map.get(
                                checkout.shipping_address_id
                            ),
                            shipping_method=shipping_method_map.get(
                                checkout.shipping_method_id
                            ),
                            valid_shipping_methods=[],
                            shipping_method_channel_listings=(
                                shipping_method_channel_listing_map.get(
                                    (checkout.shipping_method_id, channel.id)
                                ),
                            ),
                        )
                    return [checkout_info_map[key] for key in keys]

                return Promise.all(
                    [
                        addresses,
                        users,
                        shipping_methods,
                        shipping_method_channel_listings,
                    ]
                ).then(with_checkout_info)

            return (
                ChannelByIdLoader(self.context)
                .load_many(channel_pks)
                .then(with_channel)
            )

        return CheckoutByTokenLoader(self.context).load_many(keys).then(with_checkout)


class CheckoutLineByIdLoader(DataLoader):
    context_key = "checkout_line_by_id"

    def batch_load(self, keys):
        checkout_lines = CheckoutLine.objects.in_bulk(keys)
        return [checkout_lines.get(line_id) for line_id in keys]


class CheckoutLinesByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlines_by_checkout"

    def batch_load(self, keys):
        lines = CheckoutLine.objects.filter(checkout_id__in=keys)
        line_map = defaultdict(list)
        for line in lines.iterator():
            line_map[line.checkout_id].append(line)
        return [line_map.get(checkout_id, []) for checkout_id in keys]
