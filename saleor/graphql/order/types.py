import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from ...order import models
from ..core.types import CountableDjangoObjectType


class Order(CountableDjangoObjectType):
    order_id = graphene.Int(
        description='Order number.')

    class Meta:
        description = """Represents a version of a product such as different
        size or color."""
        interfaces = [relay.Node]
        model = models.Order
        exclude_fields = []

    def resolve_order_id(self, info):
        return self.pk


class OrderLine(DjangoObjectType):
    class Meta:
        model = models.OrderLine


class OrderNote(DjangoObjectType):
    class Meta:
        model = models.OrderNote
