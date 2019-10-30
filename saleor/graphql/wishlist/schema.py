import graphene

from ..core.fields import PrefetchingConnectionField
from .mutations import (
    WishlistAddProductVariantMutation,
    WishlistRemoveProductVariantMutation,
)
from .resolvers import resolve_wishlist_items
from .types import WishlistItem


class WishlistQueries(graphene.ObjectType):
    wishlist_items = PrefetchingConnectionField(
        WishlistItem, description="Get wishlist items of the current user."
    )

    def resolve_wishlist_items(self, info, **kwargs):
        return resolve_wishlist_items(info)


class WishlistMutations(graphene.ObjectType):
    wishlist_add_variant = WishlistAddProductVariantMutation.Field()
    wishlist_remove_variant = WishlistRemoveProductVariantMutation.Field()
