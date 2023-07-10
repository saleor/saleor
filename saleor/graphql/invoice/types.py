import graphene

from ...invoice import models
from ..core.descriptions import ADDED_IN_310
from ..core.types import Job, ModelObjectType
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderByIdLoader


class Invoice(ModelObjectType[models.Invoice]):
    number = graphene.String(description="Invoice number.")
    external_url = graphene.String(description="URL to view an invoice.")
    created_at = graphene.DateTime(
        required=True, description="Date and time at which invoice was created."
    )
    updated_at = graphene.DateTime(
        required=True, description="Date and time at which invoice was updated."
    )
    message = graphene.String(description="Message associated with an invoice.")
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
