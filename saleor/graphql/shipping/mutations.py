import graphene

from ...shipping import models
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types import Decimal


class ShippingPriceInput(graphene.InputObjectType):
    country_code = graphene.String(
        description='Shipping specific country code.')
    price = Decimal(description='Shipping price to a specified country.')
    shipping_method = graphene.ID(description='Related shipping method name.')


class ShippingMethodInput(graphene.InputObjectType):
    name = graphene.String(description='Shipping method\'s name.')
    description = graphene.String(
        description='Optional short description of the method.')


class ShippingMethodCreate(ModelMutation):
    class Arguments:
        input = ShippingMethodInput(
            description='Fields required to create a shipping method.',
            required=True)

    class Meta:
        description = 'Creates a new shipping method.'
        model = models.ShippingMethod

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.edit_shipping')


class ShippingMethodUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description='ID of a shipping method to update.', required=True)
        input = ShippingMethodInput(
            description='Fields required to update a shipping method.',
            required=True)

    class Meta:
        description = 'Updates a new shipping method.'
        model = models.ShippingMethod

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.edit_shipping')


class ShippingMethodDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a shipping method to delete.')

    class Meta:
        description = 'Deletes a shipping method.'
        model = models.ShippingMethod

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.edit_shipping')


class ShippingPriceCreate(ModelMutation):
    class Arguments:
        input = ShippingPriceInput(
            description='Fields required to create a shipping price',
            required=True)

    class Meta:
        description = 'Creates a new shipping price.'
        model = models.ShippingMethodCountry

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.edit_shipping')


class ShippingPriceUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description='ID of a shipping price to update.', required=True)
        input = ShippingPriceInput(
            description='Fields required to update a shipping price',
            required=True)

    class Meta:
        description = 'Updates a new shipping price.'
        model = models.ShippingMethodCountry

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.edit_shipping')


class ShippingPriceDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a shipping price to delete.')

    class Meta:
        description = 'Deletes a shipping price.'
        model = models.ShippingMethodCountry

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.edit_page')
