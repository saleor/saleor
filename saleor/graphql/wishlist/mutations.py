import graphene
from django.core.exceptions import ValidationError

from ...product.error_codes import ProductErrorCode
from ...product.utils import get_products_ids_without_variants
from ..core.mutations import BaseMutation
from ..core.types.common import WishlistError
from ..product.types import Product, ProductVariant
from .resolvers import resolve_wishlist_from_info
from .types import WishlistItem


class _BaseWishlistMutation(BaseMutation):
    wishlist = graphene.List(
        WishlistItem, description="The wishlist of the current user."
    )

    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated


class _BaseWishlistProductMutation(_BaseWishlistMutation):
    class Meta:
        abstract = True

    class Arguments:
        product_id = graphene.ID(description="The ID of the product.", required=True)


class WishlistAddProductMutation(_BaseWishlistProductMutation):
    class Meta:
        description = "Add product to the current user's wishlist."
        error_type_class = WishlistError
        error_type_field = "wishlist_errors"

    @classmethod
    def perform_mutation(cls, _root, info, product_id):  # pylint: disable=W0221
        wishlist = resolve_wishlist_from_info(info)
        product = cls.get_node_or_error(
            info, product_id, only_type=Product, field="product_id"
        )
        cls.clean_products([product])
        wishlist.add_product(product)
        wishlist_items = wishlist.items.all()
        return WishlistAddProductMutation(wishlist=wishlist_items)

    @classmethod
    def clean_products(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=ProductErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT,
                        params={"products": products_ids_without_variants},
                    )
                }
            )


class WishlistRemoveProductMutation(_BaseWishlistProductMutation):
    class Meta:
        description = "Remove product from the current user's wishlist."
        error_type_class = WishlistError
        error_type_field = "wishlist_errors"

    @classmethod
    def perform_mutation(cls, _root, info, product_id):  # pylint: disable=W0221
        wishlist = resolve_wishlist_from_info(info)
        product = cls.get_node_or_error(
            info, product_id, only_type=Product, field="product_id"
        )
        wishlist.remove_product(product)
        wishlist_items = wishlist.items.all()
        return WishlistRemoveProductMutation(wishlist=wishlist_items)


class _BaseWishlistVariantMutation(_BaseWishlistMutation):
    class Meta:
        abstract = True

    class Arguments:
        variant_id = graphene.ID(
            description="The ID of the product variant.", required=True
        )


class WishlistAddProductVariantMutation(_BaseWishlistVariantMutation):
    class Meta:
        description = "Add product variant to the current user's wishlist."
        error_type_class = WishlistError
        error_type_field = "wishlist_errors"

    @classmethod
    def perform_mutation(cls, _root, info, variant_id):  # pylint: disable=W0221
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
    def perform_mutation(cls, _root, info, variant_id):  # pylint: disable=W0221
        wishlist = resolve_wishlist_from_info(info)
        variant = cls.get_node_or_error(
            info, variant_id, only_type=ProductVariant, field="variant_id"
        )
        wishlist.remove_variant(variant)
        wishlist_items = wishlist.items.all()
        return WishlistRemoveProductVariantMutation(wishlist=wishlist_items)
