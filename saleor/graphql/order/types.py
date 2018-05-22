import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from ...order import models
from ..core.types import CountableDjangoObjectType


class Order(CountableDjangoObjectType):
    order_id = graphene.Int(
        description='Order number.')

    class Meta:
        description = 'Represents an order in the shop.'
        interfaces = [relay.Node]
        model = models.Order
        exclude_fields = []

    def resolve_order_id(self, info):
        return self.pk


class OrderLine(DjangoObjectType):
    class Meta:
        description = 'Represents order line of particular order.'
        model = models.OrderLine
        exclude_fields = ['variant']


class OrderNote(DjangoObjectType):
    class Meta:
        description = 'Note from customer or staff user.'
        model = models.OrderNote
