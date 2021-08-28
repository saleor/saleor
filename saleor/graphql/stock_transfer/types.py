import graphene

from ..core.connection import CountableDjangoObjectType
from ..meta.types import ObjectWithMetadata
from ...stock_transfer.models import StockTransfer


class StockTransferInput(graphene.InputObjectType):
    request_name = graphene.String(required=True)
    is_active = graphene.Boolean(required=False)
    approved = graphene.Boolean(required=False)
    stock_start = graphene.String(required=True)
    stock_target = graphene.String(required=True)


class UpdateStockTransferInput(graphene.InputObjectType):
    is_active = graphene.Boolean(required=False)
    approved = graphene.Boolean(required=True)


class StockTransfer(CountableDjangoObjectType):
    class Meta:
        model = StockTransfer
        only_fields = ["id", "request_name", "is_active", "approved", "stock_start",
                       "stock_target"]
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
