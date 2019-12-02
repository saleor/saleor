import graphene

from ...stock import models
from ..core.connection import CountableDjangoObjectType


class StockInput(graphene.InputObjectType):
    product_variant = graphene.ID(
        required=True, description="Product variant assiociated with stock."
    )
    warehouse = graphene.ID(
        required=True, description="Warehouse in which stock is lockated."
    )
    quantity = graphene.ID(description="Amount of items available for sell.")
    quantity_allocated = graphene.ID()


class Stock(CountableDjangoObjectType):
    class Meta:
        description = "Represents stock."
        model = models.Stock
        interfaces = [graphene.relay.Node]
