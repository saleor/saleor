import graphene

from ....core.permissions import ProductPermissions
from ....graphql.core.types import Money, MoneyRange
from ....product import models
from ....product.utils.costs import get_margin_for_variant, get_product_costs_data
from ...channel.dataloaders import (
    ChannelByProductChannelListingIDLoader,
    ChannelByProductVariantChannelListingIDLoader,
)
from ...core.connection import CountableDjangoObjectType
from ...decorators import permission_required


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
        return ChannelByProductChannelListingIDLoader(info.context).load(root.id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_purchase_cost(root: models.ProductChannelListing, *_args):
        # TODO: Add dataloader.
        variants = root.product.variants.all().values_list("id", flat=True)
        channel_listings = models.ProductVariantChannelListing.objects.filter(
            variant_id__in=variants, channel_id=root.channel_id
        )
        has_variants = True if len(variants) > 0 else False
        purchase_cost, _ = get_product_costs_data(channel_listings, has_variants)
        return purchase_cost

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.ProductChannelListing, *_args):
        # TODO: Add dataloader.
        variants = root.product.variants.all().values_list("id", flat=True)
        channel_listings = models.ProductVariantChannelListing.objects.filter(
            variant_id__in=variants, channel_id=root.channel_id
        )
        has_variants = True if len(variants) > 0 else False
        _, margin = get_product_costs_data(channel_listings, has_variants)
        return Margin(margin[0], margin[1])

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
        return ChannelByProductVariantChannelListingIDLoader(info.context).load(root.id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.ProductVariantChannelListing, *_args):
        variant_channel_listing = root.objects.filter(
            channel_id=root.channel_id
        ).first()
        if not variant_channel_listing:
            return None
        return get_margin_for_variant(variant_channel_listing)
