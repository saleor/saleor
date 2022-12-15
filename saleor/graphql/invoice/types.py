import graphene

from ...invoice import models
from ..core.types import Job, ModelObjectType
from ..meta.types import ObjectWithMetadata


class Invoice(ModelObjectType):
    number = graphene.String()
    external_url = graphene.String()
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    message = graphene.String()
    url = graphene.String(description="URL to download an invoice.")
    order_id = graphene.ID()

    class Meta:
        description = "Represents an Invoice."
        interfaces = [ObjectWithMetadata, Job, graphene.relay.Node]
        model = models.Invoice

    @staticmethod
    def resolve_order_id(root: models.Invoice, info):
        order_id = root.order_id
        return graphene.Node.to_global_id("Order", order_id) if order_id else None
