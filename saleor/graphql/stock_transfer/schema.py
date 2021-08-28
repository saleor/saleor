import graphene

from . import filters
from .mutations import StockTransferCreate, ApproveStockTransferRequest
from .types import StockTransfer
from ..core.fields import FilterInputConnectionField
from ...stock_transfer import models


class StockTransferQueries(graphene.ObjectType):
    stock_transfer = graphene.Field(
        StockTransfer,
        id=graphene.ID(required=True, description="ID of request"),
        description="Get detail for stock transfer"
    )
    stock_transfers = FilterInputConnectionField(
        StockTransfer,
        description="Get list stock transfer",
        filter=filters.StockTransferFilterInput()
    )

    def resolve_stock_transfer(self, info, **kwargs):
        stock = graphene.Node.get_node_from_global_id(info, kwargs.get("id"))
        return stock

    def resolve_stock_transfers(self, info, **_kwargs):
        return models.StockTransfer.objects.all()


class StockTransferMutation(graphene.ObjectType):
    stock_transfer_create = StockTransferCreate.Field()
    approve_stock_transfer_request = ApproveStockTransferRequest.Field()
