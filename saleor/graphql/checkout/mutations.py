import graphene
from ..core.mutations import ModelMutation
from ...checkout import models
from ..account.types import AddressInput

class CartLineInput(graphene.InputObjectType):
    quantity = graphene.Int(description='quantity')
    variant_id = graphene.ID(description='ID of product variant')


class CheckoutCreateInput(graphene.InputObjectType):
    lines = graphene.List(
        CartLineInput, description='Checkout lines')
    email = graphene.String(description='Customer email')
    shipping_address = AddressInput(description='Shipping address')


class CheckoutLineCreate(ModelMutation):
    class Arguments:
        input = CartLineInput(required=True, description='Baz')

    class Meta:
        description = 'Creates a new Checkout line'
        model = models.CartLine


class CheckoutCreate(ModelMutation):
    class Arguments:
        input = CheckoutCreateInput(
            required=True, description='Data required to create Checkout')

    class Meta:
        description = 'Create a new Checkout'
        model = models.Cart
