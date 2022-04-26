import graphene

from saleor.graphql.core.types import ModelObjectType
from saleor.graphql.meta.types import ObjectWithMetadata
from saleor.graphql.core.connection import CountableConnection
from transferrequest import models


class TransferRequest(ModelObjectType):
    id = graphene.GlobalID(required=True)
    warehouse_origin = graphene.Int(required=True)
    warehouse_destinate = graphene.Int(required=True)
    product_variant_id = graphene.Int(required=True)
    quantity = graphene.Int(required=True)
    approved = graphene.Boolean(required=False)

    class Meta:
        description = "Represents transfer request."
        model = models.TransferRequest
        interfaces = [graphene.relay.Node, ObjectWithMetadata]


class TransferRequestCountableConnection(CountableConnection):
    class Meta:
        node = TransferRequest
