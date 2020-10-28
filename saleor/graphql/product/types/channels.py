import graphene

from ....core.permissions import ProductPermissions
from ....graphql.core.types import Money, MoneyRange
from ....product import models
from ....product.utils.costs import get_margin_for_variant, get_product_costs_data
from ...channel.dataloaders import ChannelByIdLoader
from ...core.connection import CountableDjangoObjectType
from ...decorators import permission_required
from ...product.dataloaders import (
    ProductVariantsByProductIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
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
        variant_channel_listing = root.objects.filter(
            channel_id=root.channel_id
        ).first()
        if not variant_channel_listing:
            return None
        return get_margin_for_variant(variant_channel_listing)


class CollectionChannelListing(CountableDjangoObjectType):
    class Meta:
        description = "Represents collection channel listing."
        model = models.CollectionChannelListing
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "channel", "is_published", "publication_date"]

    @staticmethod
    def resolve_channel(root: models.ProductChannelListing, info, **_kwargs):
        return ChannelByIdLoader(info.context).load(root.channel_id)
