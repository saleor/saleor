from ..core.types.common import CountableDjangoObjectType
from ...checkout import models
from ...product.models import Product
from graphene import relay

class CheckoutLine(CountableDjangoObjectType):
    class Meta:
        exclude_fields = ['cart', 'data']
        description = 'Represents user address data.'
        interfaces = [relay.Node]
        model = models.CartLine


class Checkout(CountableDjangoObjectType):
    class Meta:
        description = 'Checkout object'
        model = models.Cart
        interfaces = [relay.Node]
