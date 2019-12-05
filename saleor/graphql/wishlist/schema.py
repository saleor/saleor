import graphene

from .mutations import (
    WishlistAddProductVariantMutation,
    WishlistRemoveProductVariantMutation,
)


# User's wishlist queries are located in the "saleor.graphql.account" module:
#
#     me {
#         wishlist
#     }
class WishlistQueries(graphene.ObjectType):
    pass


class WishlistMutations(graphene.ObjectType):
    wishlist_add_variant = WishlistAddProductVariantMutation.Field()
    wishlist_remove_variant = WishlistRemoveProductVariantMutation.Field()
