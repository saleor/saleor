import graphene

from saleor.graphql.core.connection import CountableDjangoObjectType
from saleor.graphql.meta.types import ObjectWithMetadata
from saleor.graphql.warehouse.types import Warehouse
from saleor.graphql.product.types import ProductVariant
from .. import models


class StockNotify(CountableDjangoObjectType):
    source_warehouse = graphene.Field(
        Warehouse,
        description="Source warehouse",
        required=True

    )

    next_warehouse = graphene.Field(
        Warehouse,
        description="Next warehouse",
        required=True

    )
    product_variant = graphene.Field(
        ProductVariant,
        description="Next warehouse",
        required=True
    )
    quantity = graphene.Int(
        description="Quantity requested"
    )
    status = graphene.Boolean(
        description="Status accepted transfer product"
    )

    class Meta:
        description = "Represents warehouse."
        model = models.StockNotify
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        only_fields = [
            "id",
        ]
