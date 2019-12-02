import graphene

from ..decorators import permission_required
from .mutations import StockBulkDelete, StockCreate, StockDelete, StockUpdate
from .types import Stock


class StockQueries(graphene.ObjectType):
    stock = graphene.Field(
        Stock,
        description="Look up a stok by ID",
        id=graphene.ID(required=True, description="ID of an warehouse"),
    )
    # TODO: Add stocks query

    @permission_required("stock.manage_stocks")
    def resolve_warehouse(self, info, **kwargs):
        stock_pk = kwargs.get("id")
        return graphene.Node.get_node_from_global_id(info, stock_pk, Stock)


class StockMutations(graphene.ObjectType):
    create_stock = StockCreate.Field()
    update_stock = StockUpdate.Field()
    delete_stock = StockDelete.Field()
    bulk_delete_stock = StockBulkDelete.Field()
