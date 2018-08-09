import graphene

from ...shipping import models
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import Decimal


class ShippingPriceInput(graphene.InputObjectType):
    name = graphene.String(
        description='Name of the shipping method.')
    price = Decimal(description='Shipping price of the shipping method.')
    shipping_zone = graphene.ID(
        description='Related shipping zone name.', name='shippingZone')


class ShippingZoneInput(graphene.InputObjectType):
    name = graphene.String(description='Shipping zone\'s name.')
    countries = graphene.List(
        graphene.String,
        description='List of countries available in the shop.')


class ShippingZoneCreate(ModelMutation):
    class Arguments:
        input = ShippingZoneInput(
            description='Fields required to create a shipping zone.',
            required=True)

    class Meta:
        description = 'Creates a new shipping zone.'
        model = models.ShippingZone

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.manage_shipping')


class ShippingZoneUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description='ID of a shipping zone to update.', required=True)
        input = ShippingZoneInput(
            description='Fields required to update a shipping zone.',
            required=True)

    class Meta:
        description = 'Updates a new shipping zone.'
        model = models.ShippingZone

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.manage_shipping')


class ShippingZoneDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a shipping zone to delete.')

    class Meta:
        description = 'Deletes a shipping zone.'
        model = models.ShippingZone

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.manage_shipping')


class ShippingPriceCreate(ModelMutation):
    class Arguments:
        input = ShippingPriceInput(
            description='Fields required to create a shipping price',
            required=True)

    class Meta:
        description = 'Creates a new shipping price.'
        model = models.ShippingMethod

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.manage_shipping')


class ShippingPriceUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description='ID of a shipping price to update.', required=True)
        input = ShippingPriceInput(
            description='Fields required to update a shipping price',
            required=True)

    class Meta:
        description = 'Updates a new shipping price.'
        model = models.ShippingMethod

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.manage_shipping')


class ShippingPriceDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a shipping price to delete.')

    class Meta:
        description = 'Deletes a shipping price.'
        model = models.ShippingMethod

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('shipping.manage_shipping')
