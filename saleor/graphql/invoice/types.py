from graphene import relay

from ...invoice import models
from ..core.connection import CountableDjangoObjectType


class Invoice(CountableDjangoObjectType):
    class Meta:
        description = "Represents an Invoice."
        interfaces = [relay.Node]
        model = models.Invoice
        only_fields = ["id", "number", "url", "status"]
