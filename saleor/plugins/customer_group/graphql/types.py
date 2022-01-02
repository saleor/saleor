import graphene
from graphene import relay
from graphene.types.objecttype import ObjectType
from graphene.types.scalars import String

from saleor.graphql.account.types import User
from saleor.graphql.core.connection import (
    CountableDjangoObjectType,
    create_connection_slice,
)
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.product.filters import ProductVariantFilterInput
from saleor.graphql.product.types import ProductVariantCountableConnection
from saleor.plugins.customer_group import models
from saleor.product.models import ProductVariant


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

    def resolve_variants(self, info, ids=None, channel=None, **kwargs):
        from saleor.graphql.channel import ChannelQsContext

        qs = ChannelQsContext(ProductVariant.objects.all(), channel)

        return create_connection_slice(
            qs, info, kwargs, ProductVariantCountableConnection
        )

    class Meta:
        model = models.CustomerGroup
        filter_fields = ["id", "name", "description"]
        interfaces = (graphene.relay.Node,)


class Customer(ObjectType):
    class Meta:
        interfaces = [relay.Node]

    name = String()


class CustomerConnection(relay.Connection):
    class Meta:
        node = User


class CustomerGroupConnection(relay.Connection):
    class Meta:
        node = CustomerGroup
