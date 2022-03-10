import graphene

from saleor.graphql.core.mutations import BaseMutation

from .. import models
from .errors import WishlistError
from .resolvers import resolve_wishlist_from_info
from .types import Wishlist


class _BaseWishlistMutation(BaseMutation):
    wishlist = graphene.Field(Wishlist, description="The wishlist of the current user.")

    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, context, permissions=None):
        return context.user.is_authenticated


class WishlistAddProductMutation(_BaseWishlistMutation):
    class Arguments:
        product_id = graphene.ID(required=True, description="Product ID.")

    class Meta:
        description = "Add a product to Wishlist catalogue"
        model = models.Wishlist
        error_type_class = WishlistError

    @classmethod
    def perform_mutation(cls, _root, info, product_id):
        wishlist = resolve_wishlist_from_info(info)
        product = cls.get_node_or_error(info, product_id, only_type="Product")
        wishlist.products.add(product)
        return cls(wishlist=wishlist)


class WishlistRemoveProductMutation(_BaseWishlistMutation):
    class Arguments:
        product_id = graphene.ID(required=True, description="Product ID.")

    class Meta:
        description = "Add a product to Wishlist catalogue"
        model = models.Wishlist
        error_type_class = WishlistError

    @classmethod
    def perform_mutation(cls, _root, info, product_id):
        wishlist = resolve_wishlist_from_info(info)
        product = cls.get_node_or_error(info, product_id, only_type="Product")
        wishlist.products.remove(product)
        return cls(wishlist=wishlist)


class WishlistAddProductVariantMutation(_BaseWishlistMutation):
    class Arguments:
        variant_id = graphene.ID(required=True, description="Product Variant ID.")

    class Meta:
        description = "Add a variant to Wishlist catalogue"
        model = models.Wishlist
        error_type_class = WishlistError

    @classmethod
    def perform_mutation(cls, _root, info, variant_id):
        wishlist = resolve_wishlist_from_info(info)
        variant = cls.get_node_or_error(info, variant_id, only_type="ProductVariant")
        wishlist.variants.add(variant)
        return cls(wishlist=wishlist)


class WishlistRemoveProductVariantMutation(_BaseWishlistMutation):
    class Arguments:
        variant_id = graphene.ID(required=True, description="Product Variant ID.")

    class Meta:
        description = "Add a variant to Wishlist catalogue"
        model = models.Wishlist
        error_type_class = WishlistError

    @classmethod
    def perform_mutation(cls, _root, info, variant_id):
        wishlist = resolve_wishlist_from_info(info)
        variant = cls.get_node_or_error(info, variant_id, only_type="ProductVariant")
        wishlist.variants.remove(variant)
        return cls(wishlist=wishlist)
