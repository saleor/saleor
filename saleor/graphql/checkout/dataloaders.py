from collections import defaultdict

from django.db.models import F
from promise import Promise

from ...checkout import CheckoutLineInfo
from ...checkout.models import Checkout, CheckoutLine
from ..core.dataloaders import DataLoader
from ..product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductVariantByIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
)


class CheckoutByTokenLoader(DataLoader):
    context_key = "checkout_by_token"

    def batch_load(self, keys):
        checkouts = Checkout.objects.filter(token__in=keys).in_bulk()
        return [checkouts[token] for token in keys]


class CheckoutLinesInfoByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlinesinfo_by_checkout"

    def batch_load(self, keys):
        from ..channel.dataloaders import ChannelByCheckoutLineIDLoader

        def with_checkout_lines(checkout_lines):
            variants_pks = list(
                {line.variant_id for lines in checkout_lines for line in lines}
            )
            if not variants_pks:
                return [[] for _ in keys]
            channel = ChannelByCheckoutLineIDLoader(self.context).load(
                checkout_lines[0][0].id
            )

            def map_variant_ids_with_channel(channel):
                def with_variants_products_collections(results):
                    variants, products, collections, channel_listings = results
                    variants_map = dict(zip(variants_pks, variants))
                    products_map = dict(zip(variants_pks, products))
                    collections_map = dict(zip(variants_pks, collections))
                    channel_listings_map = dict(zip(variants_pks, channel_listings))

                    lines_info = []
                    for lines in checkout_lines:
                        lines_info.append(
                            [
                                CheckoutLineInfo(
                                    line=line,
                                    variant=variants_map[line.variant_id],
                                    channel_listing=channel_listings_map[
                                        line.variant_id
                                    ],
                                    product=products_map[line.variant_id],
                                    collections=collections_map[line.variant_id],
                                )
                                for line in lines
                            ]
                        )
                    return lines_info

                variants = ProductVariantByIdLoader(self.context).load_many(
                    variants_pks
                )
                products = ProductByVariantIdLoader(self.context).load_many(
                    variants_pks
                )
                collections = CollectionsByVariantIdLoader(self.context).load_many(
                    variants_pks
                )

                variant_ids_channel_slug = [
                    (variant_pk, channel.slug) for variant_pk in variants_pks
                ]
                channel_listings = VariantChannelListingByVariantIdAndChannelSlugLoader(
                    self.context
                ).load_many(variant_ids_channel_slug)
                return Promise.all(
                    [variants, products, collections, channel_listings]
                ).then(with_variants_products_collections)

            return channel.then(map_variant_ids_with_channel)

        return (
            CheckoutLinesByCheckoutTokenLoader(self.context)
            .load_many(keys)
            .then(with_checkout_lines)
        )


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
