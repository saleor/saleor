import graphene

from ..core.mutations import BaseMutation
from ..core.types.common import WishlistError
from ..product.types import ProductVariant
from .resolvers import resolve_wishlist_from_info
from .types import WishlistItem


class _BaseWishlistVariantMutation(BaseMutation):
    wishlist = graphene.List(
        WishlistItem, description="The wishlist of the current user."
    )

    class Arguments:
        variant_id = graphene.ID(
            description="The ID of the product variant.", required=True
        )

    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated


class WishlistAddProductVariantMutation(_BaseWishlistVariantMutation):
    class Meta:
        description = "Add product variant to the current user's wishlist."
        error_type_class = WishlistError
        error_type_field = "wishlist_errors"

    @classmethod
    def perform_mutation(cls, _root, info, variant_id):
        wishlist = resolve_wishlist_from_info(info)
        variant = cls.get_node_or_error(
            info, variant_id, only_type=ProductVariant, field="variant_id"
        )
        wishlist.add_variant(variant)
        wishlist_items = wishlist.items.all()
        return WishlistAddProductVariantMutation(wishlist=wishlist_items)


class WishlistRemoveProductVariantMutation(_BaseWishlistVariantMutation):
    class Meta:
        description = "Remove product variant from the current user's wishlist."
        error_type_class = WishlistError
        error_type_field = "wishlist_errors"

    @classmethod
    def perform_mutation(cls, _root, info, variant_id):
        wishlist = resolve_wishlist_from_info(info)
        variant = cls.get_node_or_error(
            info, variant_id, only_type=ProductVariant, field="variant_id"
        )
        wishlist.remove_variant(variant)
        wishlist_items = wishlist.items.all()
        return WishlistRemoveProductVariantMutation(wishlist=wishlist_items)
