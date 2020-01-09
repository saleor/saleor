import graphene

from ...core.permissions import StockPermissions
from ...stock import models
from ...stock.availability import get_available_quantity_for_customer
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
    quantity_allocated = graphene.Int(description="Quantity allocated for orders.")


class Stock(CountableDjangoObjectType):
    available = graphene.Int(description="Quantity of a product available for sale.")

    class Meta:
        description = "Represents stock."
        model = models.Stock
        interfaces = [graphene.relay.Node]

    @staticmethod
    @permission_required(StockPermissions.MANAGE_STOCKS)
    def resolve_available(root, *_args):
        return get_available_quantity_for_customer(root)
