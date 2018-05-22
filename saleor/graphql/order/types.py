import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from ...order import models
from ..core.types import CountableDjangoObjectType


class Order(CountableDjangoObjectType):
    is_paid = graphene.Boolean(description='Information if order is paid.')
    order_id = graphene.Int(
        description='Order number.')
    payment_status = graphene.String(description='Information about payment')
    payment_status_display = graphene.String(
        description='Translated payment status')
    status_display = graphene.String(description='Translated status display.')

    class Meta:
        description = 'Represents an order in the shop.'
        interfaces = [relay.Node]
        model = models.Order
        exclude_fields = [
            'shipping_price_gross', 'shipping_price_net', 'total_gross',
            'total_net']

    def resolve_is_paid(self, info):
        return self.is_fully_paid()

    def resolve_order_id(self, info):
        return self.pk

    def resolve_payment_status(self, info):
        return self.get_last_payment_status()

    def resolve_payment_status_display(self, info):
        return self.get_last_payment_status_display()

    def resolve_status_display(self, info):
        return self.get_status_display()


class OrderHistoryEntry(DjangoObjectType):
    class Meta:
        description = 'History log of the order.'
        model = models.OrderHistoryEntry
        exclude_fields = ['order']


class OrderLine(DjangoObjectType):
    class Meta:
        description = 'Represents order line of particular order.'
        model = models.OrderLine
        exclude_fields = ['variant', 'unit_price_gross', 'unit_price_net']


class OrderNote(DjangoObjectType):
    class Meta:
        description = 'Note from customer or staff user.'
        model = models.OrderNote


class Fulfillment(DjangoObjectType):
    class Meta:
        description = 'Represents order fulfillment.'
        model = models.Fulfillment


class FulfillmentLine(DjangoObjectType):
    class Meta:
        description = 'Represents line of the fulfillment.'
        model = models.FulfillmentLine
