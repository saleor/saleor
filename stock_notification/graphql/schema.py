import graphene

from saleor.graphql.core.fields import FilterInputConnectionField
from .mutations import CreateTransferStock
from .types import StockNotify


class TransferStockQueries(graphene.ObjectType):
    transfer_stock_request = FilterInputConnectionField(
        StockNotify,
        description="List of stock request"
    )


class TransferStockMutations(graphene.ObjectType):
    create_transfer_stock = CreateTransferStock.Field()
