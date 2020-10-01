import graphene

from ....core.permissions import ProductPermissions
from ....graphql.core.types import Money, MoneyRange
from ....product import models
from ....product.utils.costs import get_product_costs_data
from ...channel.dataloaders import (
    ChannelByProductChannelListingIDLoader,
    ChannelByProductVariantChannelListingIDLoader,
)
from ...core.connection import CountableDjangoObjectType
from ...decorators import permission_required
from ..resolvers import resolve_margin


class Margin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class ProductChannelListing(CountableDjangoObjectType):
    discounted_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    purchase_cost = graphene.Field(MoneyRange, description="Purchase cost of product.")
    margin = graphene.Field(Margin, description="Gross margin percentage value.")

    class Meta:
        description = "Represents product channel listing."
        model = models.ProductChannelListing
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "channel", "is_published", "publication_date"]

    @staticmethod
    def resolve_channel(root: models.ProductChannelListing, info, **_kwargs):
        return ChannelByProductChannelListingIDLoader(info.context).load(root.id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_purchase_cost(root: models.ProductChannelListing, *_args):
        purchase_cost, _ = get_product_costs_data(root, root.channel.slug)
        return purchase_cost

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.ProductChannelListing, *_args):
        _, margin = get_product_costs_data(root, root.channel.slug)
        return Margin(margin[0], margin[1])


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
        return resolve_margin(root, root.channel.slug)
