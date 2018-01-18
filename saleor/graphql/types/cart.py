import graphene
from graphene import relay
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...cart.models import Cart, CartLine
from ...cart.utils import get_cart_from_request
from ..utils import DjangoPkInterface


class CartLine(DjangoObjectType):
    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = CartLine


class CartType(DjangoObjectType):
    lines = DjangoConnectionField(CartLine)

    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = Cart


def resolve_cart(info):
    return get_cart_from_request(info.context, Cart.objects.for_display())
