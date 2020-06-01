import graphene

from ...invoice import models
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import Job


class Invoice(CountableDjangoObjectType):
    url = graphene.String()

    class Meta:
        description = "Represents an Invoice."
        interfaces = [Job]
        model = models.Invoice
        only_fields = [
            "id",
            "number",
            "external_url",
            "status",
            "pending_target",
            "metadata",
        ]
