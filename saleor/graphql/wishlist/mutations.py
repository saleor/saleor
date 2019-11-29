import graphene

from ..core.mutations import BaseMutation
from ..core.types.common import WishlistError
from ..product.types import ProductVariant
from .resolvers import get_wishlist_from_info
from .types import WishlistItem


class WishlistAddProductVariantMutation(BaseMutation):
    wishlist_items = graphene.List(
        WishlistItem, description="The list of WishlistItems of the current user."
    )

    class Arguments:
        variant_id = graphene.ID(
            description="The ID of the ProductVariant.", required=True
        )

    class Meta:
        description = "Add ProductVariant to the current user's Wishlist."
        error_type_class = WishlistError
        error_type_field = "wishlist_errors"

    @classmethod
    def perform_mutation(cls, _root, info, variant_id):
        wishlist = get_wishlist_from_info(info)
        variant = cls.get_node_or_error(
            info, variant_id, only_type=ProductVariant, field="variant_id"
        )
        wishlist.add_variant(variant)
        wishlist_items = wishlist.items.all()
        return WishlistAddProductVariantMutation(wishlist_items=wishlist_items)


class WishlistRemoveProductVariantMutation(BaseMutation):
    wishlist_items = graphene.List(
        WishlistItem, description="The list of WishlistItems of the current user."
    )

    class Arguments:
        variant_id = graphene.ID(
            description="The ID of the ProductVariant.", required=True
        )

    class Meta:
        description = "Remove ProductVariant from the current user's wishlist."
        error_type_class = WishlistError
        error_type_field = "wishlist_errors"

    @classmethod
    def perform_mutation(cls, _root, info, variant_id):
        wishlist = get_wishlist_from_info(info)
        variant = cls.get_node_or_error(
            info, variant_id, only_type=ProductVariant, field="variant_id"
        )
        wishlist.remove_variant(variant)
        wishlist_items = wishlist.items.all()
        return WishlistRemoveProductVariantMutation(wishlist_items=wishlist_items)
