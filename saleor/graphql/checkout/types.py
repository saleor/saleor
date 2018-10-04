import graphene

from ...checkout import models
from ...core.utils.taxes import get_taxes_for_address
from ..core.types.common import CountableDjangoObjectType
from ..core.types.money import TaxedMoney


class CheckoutLine(CountableDjangoObjectType):
    total_price = graphene.Field(
        TaxedMoney,
        description=(
            'The sum of the checkout line price, taxes and discounts.'))
    requires_shipping = graphene.Boolean(
        description='Indicates whether the item need to be delivered.')

    class Meta:
        exclude_fields = ['cart', 'data']
        description = 'Represents an item in the checkout.'
        interfaces = [graphene.relay.Node]
        model = models.CartLine
        filter_fields = ['id']

    def resolve_total_price(self, info):
        taxes = get_taxes_for_address(self.cart.shipping_address)
        return self.get_total(taxes=taxes)

    def resolve_requires_shipping(self, info):
        return self.is_shipping_required()


class Checkout(CountableDjangoObjectType):
    total_price = graphene.Field(
        TaxedMoney,
        description=(
            'The sum of the the checkout line prices, with all the taxes,'
            'shipping costs, and discounts included.'))
    subtotal_price = graphene.Field(
        TaxedMoney,
        description=(
            'The price of the checkout before shipping, with taxes included.'))
    shipping_price = graphene.Field(
        TaxedMoney,
        description='The price of the shipping, with all the taxes included.')
    lines = graphene.List(
        CheckoutLine, description=(
            'A list of checkout lines, each containing information about '
            'an item in the checkout.'))

    class Meta:
        description = 'Checkout object'
        model = models.Cart
        interfaces = [graphene.relay.Node]
        filter_fields = ['token']

    def resolve_total_price(self, info):
        taxes = get_taxes_for_address(self.shipping_address)
        return self.get_total(taxes=taxes)

    def resolve_subtotal_price(self, info):
        taxes = get_taxes_for_address(self.shipping_address)
        return self.get_subtotal(taxes=taxes)

    def resolve_shipping_price(self, info):
        taxes = get_taxes_for_address(self.shipping_address)
        return self.get_shipping_price(taxes=taxes)

    def resolve_lines(self, info):
        return self.lines.prefetch_related('variant')
