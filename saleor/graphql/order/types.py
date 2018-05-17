from ..core.types import CountableDjangoObjectType
from graphene import relay

from ...order import models

class Order(CountableDjangoObjectType):

    class Meta:
        description = """Represents a version of a product such as different
        size or color."""
        interfaces = [relay.Node]
        model = models.Order
        exclude_fields = []
