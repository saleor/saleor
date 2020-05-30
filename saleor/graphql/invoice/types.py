import graphene

from ...invoice import models
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import Job


class Invoice(CountableDjangoObjectType):
    url = graphene.String()

    class Meta:
        description = "Represents an Invoice."
        interfaces = [graphene.relay.Node]
        model = models.Invoice
        only_fields = ["id", "number", "url", "metadata"]


class InvoiceJob(CountableDjangoObjectType):
    invoice = graphene.Field(Invoice, description="Invoice object related to the job.")

    class Meta:
        description = "Represents an invoice job."
        interfaces = [graphene.relay.Node, Job]
        model = models.InvoiceJob
        only_fields = ["id", "status", "invoice", "pending_target"]
