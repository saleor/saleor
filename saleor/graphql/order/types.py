import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from ...order import models
from ..core.types import CountableDjangoObjectType, Money, TaxedMoney


class Order(CountableDjangoObjectType):
    is_paid = graphene.Boolean(
        description='Informs if an order is fully paid.')
    order_id = graphene.Int(
        description='User-friendly ID of an order.')
    payment_status = graphene.String(description='Internal payment status.')
    payment_status_display = graphene.String(
        description='User-friendly payment status.')
    status_display = graphene.String(
        description='User-friendly order status.')
    captured_amount = graphene.Field(
        Money, description='Amount captured by payment.')
    total_price = graphene.Field(
        TaxedMoney, description='Total price of the order.')

    class Meta:
        description = 'Represents an order in the shop.'
        interfaces = [relay.Node]
        model = models.Order
        exclude_fields = [
            'shipping_price_gross', 'shipping_price_net', 'total_gross',
            'total_net']

    def resolve_captured_amount(self, info):
        payment = self.get_last_payment()
        if payment:
            return payment.get_captured_price()

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

    def resolve_total_prize(self, info):
        payment = self.get_last_payment()
        if payment:
            return payment.get_total_price()


class OrderHistoryEntry(CountableDjangoObjectType):
    class Meta:
        description = 'History log of the order.'
        model = models.OrderHistoryEntry
        interfaces = [relay.Node]
        exclude_fields = ['order']


class OrderLine(CountableDjangoObjectType):
    class Meta:
        description = 'Represents order line of particular order.'
        model = models.OrderLine
        interfaces = [relay.Node]
        exclude_fields = [
            'variant', 'unit_price_gross', 'unit_price_net', 'order']


class OrderNote(CountableDjangoObjectType):
    class Meta:
        description = 'Note from customer or staff user.'
        model = models.OrderNote
        interfaces = [relay.Node]
        exclude_fields = ['order']


class Fulfillment(CountableDjangoObjectType):
    status_display = graphene.String(
        description='User-friendly fulfillment status.')

    class Meta:
        description = 'Represents order fulfillment.'
        interfaces = [relay.Node]
        model = models.Fulfillment
        exclude_fields = ['order']

    def resolve_status_display(self, info):
        return self.get_status_display()


class FulfillmentLine(CountableDjangoObjectType):
    class Meta:
        description = 'Represents line of the fulfillment.'
        interfaces = [relay.Node]
        model = models.FulfillmentLine
        exclude_fields = ['fulfillment']
