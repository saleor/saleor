import graphene
from graphene import relay

from saleor.graphql.core.connection import (
    CountableDjangoObjectType,
    create_connection_slice,
)
from saleor.graphql.core.fields import ConnectionField
from saleor.product.models import Product, ProductVariant

from .. import models


class ProductWishlistType(CountableDjangoObjectType):
    class Meta:
        interfaces = (graphene.relay.Node,)
        model = Product
        only_fields = [
            "category",
            "charge_taxes",
            "description",
            "id",
            "name",
            "slug",
            "product_type",
            "seo_description",
            "seo_title",
            "updated_at",
            "weight",
            "default_variant",
            "rating",
        ]


class ProductWishlistTypeConnection(relay.Connection):
    class Meta:
        node = ProductWishlistType


class VariantWishlistType(CountableDjangoObjectType):
    class Meta:
        interfaces = (graphene.relay.Node,)
        model = ProductVariant
        only_fields = [
            "id",
            "name",
            "track_inventory",
            "is_preorder",
            "preorder_end_date",
            "preorder_global_threshold",
            "quantity_limit_per_customer",
            "weight",
        ]


class VariantWishlistTypeConnection(relay.Connection):
    class Meta:
        node = VariantWishlistType


class Wishlist(CountableDjangoObjectType):
    products = ConnectionField(
        ProductWishlistTypeConnection,
        description="List of product variants.",
    )
    variants = ConnectionField(
        VariantWishlistTypeConnection,
        description="List of product variants.",
    )

    class Meta:
        model = models.Wishlist
        filter_fields = [
            "id",
            "token",
        ]
        interfaces = (graphene.relay.Node,)
        exclude = ["user", "token"]

    def resolve_variants(root, info, ids=None, channel=None, **kwargs):
        groups = models.Wishlist.objects.get(pk=root.id)
        qs = groups.variants.all()
        return create_connection_slice(qs, info, kwargs, VariantWishlistTypeConnection)

    def resolve_products(root, info, ids=None, channel=None, **kwargs):
        groups = models.Wishlist.objects.get(pk=root.id)

        qs = groups.products.all()
        return create_connection_slice(qs, info, kwargs, ProductWishlistTypeConnection)
