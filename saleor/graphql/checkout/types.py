import graphene

from ...checkout import models
from ..core.types.common import CountableDjangoObjectType
from ..core.types.money import TaxedMoney
from ...core.utils.taxes import get_taxes_for_address


class CheckoutLine(CountableDjangoObjectType):
    total_price = graphene.Field(TaxedMoney, description='Total price')
    requires_shipping = graphene.Boolean(description='Line requires shipping')

    class Meta:
        exclude_fields = ['cart', 'data']
        description = 'Represents user address data.'
        interfaces = [graphene.relay.Node]
        model = models.CartLine
        filter_fields = ['id']


    def resolve_total_price(self, info):
        taxes = get_taxes_for_address(self.cart.shipping_address)
        return self.get_total(taxes=taxes)

    def resolve_requires_shipping(self, info):
        return self.is_shipping_required()


class Checkout(CountableDjangoObjectType):
    total_price = graphene.Field(TaxedMoney, description='Total price')
    subtotal_price = graphene.Field(
        TaxedMoney, description='Total without shipping')
    shipping_price = graphene.Field(TaxedMoney, description='Shipping price')

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
