import graphene
import graphene_django_optimizer as gql_optimizer
from django.conf import settings

from ...checkout import models
from ...core.utils.taxes import get_taxes_for_address
from ..core.connection import CountableDjangoObjectType
from ..core.types.money import TaxedMoney
from ..order.utils import applicable_shipping_methods
from ..payment.enums import PaymentGatewayEnum
from ..shipping.types import ShippingMethod


class CheckoutLine(CountableDjangoObjectType):
    total_price = graphene.Field(
        TaxedMoney,
        description=(
            'The sum of the checkout line price, taxes and discounts.'))
    requires_shipping = graphene.Boolean(
        description='Indicates whether the item need to be delivered.')

    class Meta:
        only_fields = ['id', 'quantity', 'variant']
        description = 'Represents an item in the checkout.'
        interfaces = [graphene.relay.Node]
        model = models.CheckoutLine
        filter_fields = ['id']

    def resolve_total_price(self, info):
        taxes = get_taxes_for_address(self.checkout.shipping_address)
        return self.get_total(discounts=info.context.discounts, taxes=taxes)

    def resolve_requires_shipping(self, *_args):
        return self.is_shipping_required()


class Checkout(CountableDjangoObjectType):
    available_shipping_methods = graphene.List(
        ShippingMethod, required=True,
        description='Shipping methods that can be used with this order.')
    available_payment_gateways = graphene.List(
        PaymentGatewayEnum, description='List of available payment gateways.',
        required=True)
    email = graphene.String(description='Email of a customer', required=True)
    is_shipping_required = graphene.Boolean(
        description='Returns True, if checkout requires shipping.',
        required=True)
    lines = gql_optimizer.field(
        graphene.List(
            CheckoutLine, description=(
                'A list of checkout lines, each containing information about '
                'an item in the checkout.')),
        model_field='lines')
    shipping_price = graphene.Field(
        TaxedMoney,
        description='The price of the shipping, with all the taxes included.')
    subtotal_price = graphene.Field(
        TaxedMoney,
        description=(
            'The price of the checkout before shipping, with taxes included.'))
    total_price = graphene.Field(
        TaxedMoney,
        description=(
            'The sum of the the checkout line prices, with all the taxes,'
            'shipping costs, and discounts included.'))

    class Meta:
        only_fields = [
            'billing_address', 'created', 'discount_amount', 'discount_name',
            'is_shipping_required', 'last_change', 'note', 'quantity',
            'shipping_address', 'shipping_method', 'token',
            'translated_discount_name', 'user', 'voucher_code']
        description = 'Checkout object'
        model = models.Checkout
        interfaces = [graphene.relay.Node]
        filter_fields = ['token']

    def resolve_total_price(self, info):
        taxes = get_taxes_for_address(self.shipping_address)
        return self.get_total(discounts=info.context.discounts, taxes=taxes)

    def resolve_subtotal_price(self, *_args):
        taxes = get_taxes_for_address(self.shipping_address)
        return self.get_subtotal(taxes=taxes)

    def resolve_shipping_price(self, *_args):
        taxes = get_taxes_for_address(self.shipping_address)
        return self.get_shipping_price(taxes=taxes)

    def resolve_lines(self, *_args):
        return self.lines.prefetch_related('variant')

    def resolve_available_shipping_methods(self, info):
        taxes = get_taxes_for_address(self.shipping_address)
        price = self.get_subtotal(
            taxes=taxes, discounts=info.context.discounts)
        return applicable_shipping_methods(self, price.gross.amount)

    def resolve_available_payment_gateways(self, _info):
        return settings.CHECKOUT_PAYMENT_GATEWAYS.keys()

    def resolve_is_shipping_required(self, _info):
        return self.is_shipping_required()
