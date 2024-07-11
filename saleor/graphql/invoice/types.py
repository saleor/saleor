import graphene

from ...invoice import models
from ..core.descriptions import ADDED_IN_310, DEPRECATED_IN_3X_FIELD
from ..core.scalars import DateTime
from ..core.types import Job, ModelObjectType
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderByIdLoader


class Invoice(ModelObjectType[models.Invoice]):
    number = graphene.String(description="Invoice number.")
    external_url = graphene.String(
        description="URL to view an invoice.",
        required=False,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `url` field."
            "This field will be removed in 4.0"
        ),
    )
    created_at = DateTime(
        required=True, description="Date and time at which invoice was created."
    )
    updated_at = DateTime(
        required=True, description="Date and time at which invoice was updated."
    )
    message = graphene.String(description="Message associated with an invoice.")
    url = graphene.String(
        description=(
            "URL to view/download an invoice. "
            "This can be an internal URL if the Invoicing Plugin was used "
            "or an external URL if it has been provided."
        )
    )
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
