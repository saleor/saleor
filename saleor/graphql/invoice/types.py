import graphene

from ...invoice import models
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import InvoiceJobInterface


class Invoice(CountableDjangoObjectType):
    class Meta:
        description = "Represents an Invoice."
        interfaces = [graphene.relay.Node]
        model = models.Invoice
        only_fields = ["id", "number", "url"]


class InvoiceJob(CountableDjangoObjectType):
    invoice = graphene.Field(Invoice, description="Invoice object related to the job.")

    class Meta:
        description = "Represents an invoice job."
        interfaces = [graphene.relay.Node, InvoiceJobInterface]
        model = models.InvoiceJob
        only_fields = ["id", "status", "invoice"]
