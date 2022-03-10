import graphene
from graphene_federation import build_schema

from .. import models
from . import types
from .mutations import (
    WishlistAddProductMutation,
    WishlistAddProductVariantMutation,
    WishlistRemoveProductMutation,
    WishlistRemoveProductVariantMutation,
)


class Query(graphene.ObjectType):

    wishlist = graphene.Field(
        types.Wishlist,
        description="Look up a wishlist by token",
    )

    def resolve_wishlist(self, info, **data):
        user = info.context.user
        return (
            models.Wishlist.objects.get(user_id=user.id)
            if user.is_authenticated
            else None
        )


class Mutation(graphene.ObjectType):
    wishlist_add_product = WishlistAddProductMutation.Field()
    wishlist_remove_product = WishlistRemoveProductMutation.Field()
    wishlist_add_variant = WishlistAddProductVariantMutation.Field()
    wishlist_remove_variant = WishlistRemoveProductVariantMutation.Field()


schema = build_schema(query=Query, mutation=Mutation, types=[types.Wishlist])
