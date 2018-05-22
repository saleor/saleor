import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from ...order import models
from ..core.types import CountableDjangoObjectType


class Order(CountableDjangoObjectType):
    order_id = graphene.Int(
        description='Order number.')
    status_display = graphene.String(description='Translated status display.')

    class Meta:
        description = 'Represents an order in the shop.'
        interfaces = [relay.Node]
        model = models.Order
        exclude_fields = [
            'shipping_price_gross', 'shipping_price_net', 'total_gross',
            'total_net']

    def resolve_order_id(self, info):
        return self.pk

    def resolve_status_display(self, info):
        return self.get_status_display()


class OrderLine(DjangoObjectType):
    class Meta:
        description = 'Represents order line of particular order.'
        model = models.OrderLine
        exclude_fields = ['variant', 'unit_price_gross', 'unit_price_net']


class OrderNote(DjangoObjectType):
    class Meta:
        description = 'Note from customer or staff user.'
        model = models.OrderNote
