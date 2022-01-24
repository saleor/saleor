import graphene

from ...wishlist import models
from ..channel import ChannelContext, ChannelQsContext
from ..core.connection import CountableDjangoObjectType, create_connection_slice
from ..core.fields import ConnectionField
from ..product.types import Product, ProductVariantCountableConnection


class Wishlist(CountableDjangoObjectType):
    class Meta:
        filter_fields = ["id"]
        model = models.Wishlist
        interfaces = [graphene.relay.Node]
        description = "Current user's wishlist."
        only_fields = ["id", "created_at", "items"]


class WishlistItem(CountableDjangoObjectType):
    variants = ConnectionField(
        ProductVariantCountableConnection,
        description="List of variants for the wishlist.",
    )
    product = graphene.Field(Product, description="Product for the wishlist item.")

    class Meta:
        filter_fields = ["id"]
        model = models.WishlistItem
        description = "Wishlist item."
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "wishlist", "product", "variants"]

    @staticmethod
    def resolve_variants(root, info, **kwargs):
        qs = ChannelQsContext(qs=root.variants.all(), channel_slug=None)
        return create_connection_slice(
            qs, info, kwargs, ProductVariantCountableConnection
        )

    @staticmethod
    def resolve_product(root, info, **kwargs):
        return (
            ChannelContext(node=root.product, channel_slug=None)
            if root.product
            else None
        )
