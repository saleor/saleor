import graphene

from ...invoice import models
from ..core.descriptions import ADDED_IN_310
from ..core.types import Job, ModelObjectType
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderByIdLoader


class Invoice(ModelObjectType[models.Invoice]):
    number = graphene.String()
    external_url = graphene.String()
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    message = graphene.String()
    url = graphene.String(description="URL to download an invoice.")
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="Order related to the invoice." + ADDED_IN_310,
    )

    class Meta:
        description = "Represents an Invoice."
        interfaces = [ObjectWithMetadata, Job, graphene.relay.Node]
        model = models.Invoice

    @staticmethod
    def resolve_order(root: models.Invoice, info):
        return OrderByIdLoader(info.context).load(root.order_id)
