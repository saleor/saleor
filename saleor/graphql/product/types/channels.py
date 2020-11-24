from dataclasses import asdict

import graphene

from saleor.graphql.product.dataloaders.products import ProductByIdLoader

from ....core.permissions import ProductPermissions
from ....graphql.core.types import Money, MoneyRange
from ....product import models
from ....product.utils.availability import get_product_availability
from ....product.utils.costs import (
    get_margin_for_variant_channel_listing,
    get_product_costs_data,
)
from ...channel.dataloaders import ChannelByIdLoader
from ...core.connection import CountableDjangoObjectType
from ...decorators import permission_required
from ...discount.dataloaders import DiscountsByDateTimeLoader
from ..dataloaders import (
    CollectionsByProductIdLoader,
    ProductVariantsByProductIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
    VariantsChannelListingByProductIdAndChanneSlugLoader,
)


class Margin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class ProductChannelListing(CountableDjangoObjectType):
    discounted_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    purchase_cost = graphene.Field(MoneyRange, description="Purchase cost of product.")
    margin = graphene.Field(Margin, description="Range of margin percentage value.")
    is_available_for_purchase = graphene.Boolean(
        description="Whether the product is available for purchase."
    )
    pricing = graphene.Field(
        "saleor.graphql.product.types.products.ProductPricingInfo",
        description=(
            "Lists the storefront product's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )

    class Meta:
        description = "Represents product channel listing."
        model = models.ProductChannelListing
        interfaces = [graphene.relay.Node]
        only_fields = [
            "id",
            "channel",
            "is_published",
            "publication_date",
            "visible_in_listings",
            "available_for_purchase",
        ]

    @staticmethod
    def resolve_channel(root: models.ProductChannelListing, info, **_kwargs):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_purchase_cost(root: models.ProductChannelListing, info, *_kwargs):
        channel = ChannelByIdLoader(info.context).load(root.channel_id)

        def calculate_margin_with_variants(variants):
            def calculate_margin_with_channel(channel):
                def calculate_margin_with_channel_listings(variant_channel_listings):
                    variant_channel_listings = list(
                        filter(None, variant_channel_listings)
                    )
                    if not variant_channel_listings:
                        return None

                    has_variants = True if len(variant_ids_channel_slug) > 0 else False
                    purchase_cost, _margin = get_product_costs_data(
                        variant_channel_listings, has_variants, root.currency
                    )
                    return purchase_cost

                variant_ids_channel_slug = [
                    (variant.id, channel.slug) for variant in variants
                ]
                return (
                    VariantChannelListingByVariantIdAndChannelSlugLoader(info.context)
                    .load_many(variant_ids_channel_slug)
                    .then(calculate_margin_with_channel_listings)
                )

            return channel.then(calculate_margin_with_channel)

        return (
            ProductVariantsByProductIdLoader(info.context)
            .load(root.product_id)
            .then(calculate_margin_with_variants)
        )

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.ProductChannelListing, info, *_kwargs):
        channel = ChannelByIdLoader(info.context).load(root.channel_id)

        def calculate_margin_with_variants(variants):
            def calculate_margin_with_channel(channel):
                def calculate_margin_with_channel_listings(variant_channel_listings):
                    variant_channel_listings = list(
                        filter(None, variant_channel_listings)
                    )
                    if not variant_channel_listings:
                        return None

                    has_variants = True if len(variant_ids_channel_slug) > 0 else False
                    _purchase_cost, margin = get_product_costs_data(
                        variant_channel_listings, has_variants, root.currency
                    )
                    return Margin(margin[0], margin[1])

                variant_ids_channel_slug = [
                    (variant.id, channel.slug) for variant in variants
                ]
                return (
                    VariantChannelListingByVariantIdAndChannelSlugLoader(info.context)
                    .load_many(variant_ids_channel_slug)
                    .then(calculate_margin_with_channel_listings)
                )

            return channel.then(calculate_margin_with_channel)

        return (
            ProductVariantsByProductIdLoader(info.context)
            .load(root.product_id)
            .then(calculate_margin_with_variants)
        )

    @staticmethod
    def resolve_is_available_for_purchase(root: models.ProductChannelListing, _info):
        return root.is_available_for_purchase()

    @staticmethod
    def resolve_pricing(root: models.ProductChannelListing, info):
        context = info.context

        def calculate_pricing_info(discounts):
            def calculate_pricing_with_channel(channel):
                def calculate_pricing_with_product(product):
                    def calculate_pricing_with_variants(variants):
                        def calculate_pricing_with_variants_channel_listings(
                            variants_channel_listing,
                        ):
                            def calculate_pricing_with_collections(collections):
                                if not variants_channel_listing:
                                    return None
                                availability = get_product_availability(
                                    product=product,
                                    product_channel_listing=root,
                                    variants=variants,
                                    variants_channel_listing=variants_channel_listing,
                                    collections=collections,
                                    discounts=discounts,
                                    channel=channel,
                                    country=context.country,
                                    local_currency=context.currency,
                                    plugins=context.plugins,
                                )
                                from .products import ProductPricingInfo

                                return ProductPricingInfo(**asdict(availability))

                            return (
                                CollectionsByProductIdLoader(context)
                                .load(root.product_id)
                                .then(calculate_pricing_with_collections)
                            )

                        return (
                            VariantsChannelListingByProductIdAndChanneSlugLoader(
                                context
                            )
                            .load((root.product_id, channel.slug))
                            .then(calculate_pricing_with_variants_channel_listings)
                        )

                    return (
                        ProductVariantsByProductIdLoader(context)
                        .load(root.product_id)
                        .then(calculate_pricing_with_variants)
                    )

                return (
                    ProductByIdLoader(context)
                    .load(root.product_id)
                    .then(calculate_pricing_with_product)
                )

            return (
                ChannelByIdLoader(context)
                .load(root.channel_id)
                .then(calculate_pricing_with_channel)
            )

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_pricing_info)
        )


class ProductVariantChannelListing(CountableDjangoObjectType):
    cost_price = graphene.Field(Money, description="Cost price of the variant.")
    margin = graphene.Int(description="Gross margin percentage value.")

    class Meta:
        description = "Represents product varaint channel listing."
        model = models.ProductVariantChannelListing
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "channel", "price", "cost_price"]

    @staticmethod
    def resolve_channel(root: models.ProductVariantChannelListing, info, **_kwargs):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.ProductVariantChannelListing, *_args):
        return get_margin_for_variant_channel_listing(root)


class CollectionChannelListing(CountableDjangoObjectType):
    class Meta:
        description = "Represents collection channel listing."
        model = models.CollectionChannelListing
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "channel", "is_published", "publication_date"]

    @staticmethod
    def resolve_channel(root: models.ProductChannelListing, info, **_kwargs):
        return ChannelByIdLoader(info.context).load(root.channel_id)
