import graphene
from graphene import relay
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...cart.models import Cart, CartLine
from ...cart.utils import get_cart_from_request
from ..utils import DjangoPkInterface, PriceField


class CartLine(DjangoObjectType):
    item_name = graphene.String()
    total = PriceField()

    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = CartLine

    def resolve_item_name(self, info):
        return '%s - %s' % (self.variant.product, self.variant)

    def resolve_total(self, info):
        return self.get_total(discounts=info.context.discounts)


class CartType(DjangoObjectType):
    lines = DjangoConnectionField(CartLine)
    total = PriceField()

    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = Cart
    
    def resolve_total(self, info):
        return self.get_total(discounts=info.context.discounts)


def resolve_cart(info):
    return get_cart_from_request(info.context, Cart.objects.for_display())
