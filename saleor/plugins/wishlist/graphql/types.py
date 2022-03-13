import graphene

from saleor.graphql.channel import ChannelQsContext
from saleor.graphql.core.connection import (
    CountableDjangoObjectType,
    create_connection_slice,
)
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.product.filters import ProductFilterInput, ProductVariantFilterInput
from saleor.graphql.product.types import (
    ProductCountableConnection,
    ProductVariantCountableConnection,
)

from .. import models


class Wishlist(CountableDjangoObjectType):
    products = FilterConnectionField(
        ProductCountableConnection,
        ids=graphene.List(
            graphene.ID, description="Filter product variants by given IDs."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        filter=ProductFilterInput(description="Filtering options for product variant."),
        description="List of product variants.",
    )
    variants = FilterConnectionField(
        ProductVariantCountableConnection,
        ids=graphene.List(
            graphene.ID, description="Filter product variants by given IDs."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        filter=ProductVariantFilterInput(
            description="Filtering options for product variant."
        ),
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
        qs = ChannelQsContext(groups.variants.all(), channel)
        return create_connection_slice(
            qs, info, kwargs, ProductVariantCountableConnection
        )

    def resolve_products(root, info, ids=None, channel=None, **kwargs):

        groups = models.Wishlist.objects.get(pk=root.id)
        qs = ChannelQsContext(groups.products.all(), channel)
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)
