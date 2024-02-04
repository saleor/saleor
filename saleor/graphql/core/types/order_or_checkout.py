import graphene

from ....checkout.models import Checkout
from ....order.models import Order
from ...checkout import types as checkout_types
from ...order import types as order_types

# The file hasn't been attached to the __init__ file as it generates the circular
# graphql import. Graphene for Union types requires already initialized types so
# we need to provide a fully initialized type.


class OrderOrCheckoutBase(graphene.Union):
    class Meta:
        abstract = True

    @classmethod
    def get_types(cls):
        return (checkout_types.Checkout, order_types.Order)

    @classmethod
    def resolve_type(cls, instance, info: graphene.ResolveInfo):
        if isinstance(instance, Checkout):
            return checkout_types.Checkout
        if isinstance(instance, Order):
            return order_types.Order
        return super().resolve_type(instance, info)


class OrderOrCheckout(OrderOrCheckoutBase):
    class Meta:
        types = OrderOrCheckoutBase.get_types()
