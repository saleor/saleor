import graphene
from graphene import relay

from saleor.graphql.core.connection import (
    CountableDjangoObjectType,
    create_connection_slice,
)
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.product.filters import ProductVariantFilterInput
from saleor.graphql.product.types import ProductVariantCountableConnection
from saleor.plugins.customer_group import models


class CustomerGroup(CountableDjangoObjectType):
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

    def resolve_variants(root, info, ids=None, channel=None, **kwargs):
        from saleor.graphql.channel import ChannelQsContext

        groups = models.CustomerGroup.objects.get(pk=root.id)
        qs = ChannelQsContext(groups.variants.all(), channel)
        return create_connection_slice(
            qs, info, kwargs, ProductVariantCountableConnection
        )

    class Meta:
        model = models.CustomerGroup
        filter_fields = ["id", "name", "description"]
        interfaces = (graphene.relay.Node,)


class CustomerGroupConnection(relay.Connection):
    class Meta:
        node = CustomerGroup
