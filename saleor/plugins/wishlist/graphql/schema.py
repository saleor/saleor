import graphene
from graphene_federation import build_schema

from saleor.graphql.account.types import User as UserType
from saleor.graphql.core.utils import from_global_id_or_error

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
        user_id=graphene.Argument(graphene.ID, description="User ID.", required=True),
        description="Look up a vendor by ID",
    )

    def resolve_wishlist(self, info, user_id, **data):
        _, id = from_global_id_or_error(user_id, UserType)
        return models.Wishlist.objects.get(user_id=id)


class Mutation(graphene.ObjectType):
    wishlist_add_product = WishlistAddProductMutation.Field()
    wishlist_remove_product = WishlistRemoveProductMutation.Field()
    wishlist_add_variant = WishlistAddProductVariantMutation.Field()
    wishlist_remove_variant = WishlistRemoveProductVariantMutation.Field()


schema = build_schema(query=Query, mutation=Mutation, types=[types.Wishlist])
