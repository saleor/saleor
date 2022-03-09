import graphene
from graphene_federation import build_schema

from . import types
from .mutations import (
    WishlistAddProductMutation,
    WishlistAddProductVariantMutation,
    WishlistRemoveProductMutation,
    WishlistRemoveProductVariantMutation,
)


class Mutation(graphene.ObjectType):
    wishlist_add_product = WishlistAddProductMutation.Field()
    wishlist_remove_product = WishlistRemoveProductMutation.Field()
    wishlist_add_variant = WishlistAddProductVariantMutation.Field()
    wishlist_remove_variant = WishlistRemoveProductVariantMutation.Field()


schema = build_schema(
    mutation=Mutation,
)
