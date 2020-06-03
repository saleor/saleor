import graphene

from ...invoice import models
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import Job
from ..meta.types import ObjectWithMetadata


class Invoice(CountableDjangoObjectType):
    url = graphene.String(description="URL to download an invoice.")

    class Meta:
        description = "Represents an Invoice."
        interfaces = [ObjectWithMetadata, Job, graphene.relay.Node]
        model = models.Invoice
        only_fields = [
            "id",
            "number",
            "external_url",
            "status",
            "metadata",
        ]
