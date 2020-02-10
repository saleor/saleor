import graphene

from .mutations import (
    WishlistAddProductMutation,
    WishlistAddProductVariantMutation,
    WishlistRemoveProductMutation,
    WishlistRemoveProductVariantMutation,
)

# User's wishlist queries are located in the "saleor.graphql.account" module:
#
#     me {
#         wishlist
#     }


class WishlistMutations(graphene.ObjectType):
    wishlist_add_product = WishlistAddProductMutation.Field()
    wishlist_remove_product = WishlistRemoveProductMutation.Field()
    wishlist_add_variant = WishlistAddProductVariantMutation.Field()
    wishlist_remove_variant = WishlistRemoveProductVariantMutation.Field()
