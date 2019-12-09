import graphene
from django.conf import settings

from ...stock import models
from ..core.connection import CountableDjangoObjectType
from ..decorators import permission_required


class StockInput(graphene.InputObjectType):
    product_variant = graphene.ID(
        required=True, description="Product variant assiociated with stock."
    )
    warehouse = graphene.ID(
        required=True, description="Warehouse in which stock is lockated."
    )
    quantity = graphene.Int(description="Quantity of items available for sell.")
    quantity_allocated = graphene.Int()


class Stock(CountableDjangoObjectType):
    available = graphene.Int(description="Quantity of a product available for sale.")

    class Meta:
        description = "Represents stock."
        model = models.Stock
        interfaces = [graphene.relay.Node]

    @staticmethod
    @permission_required("stock.manage_stocks")
    def resolve_available(root, *_args):
        return min(root.quantity_available, settings.MAX_CHECKOUT_LINE_QUANTITY)
