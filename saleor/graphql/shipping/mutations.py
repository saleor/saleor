import graphene
from textwrap import dedent

from ...dashboard.shipping.forms import default_shipping_zone_exists
from ...shipping import models
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import Decimal
from .types import ShippingMethodTypeEnum, ShippingZone, WeightScalar


class ShippingPriceInput(graphene.InputObjectType):
    name = graphene.String(
        description='Name of the shipping method. Visible to customers')
    price = Decimal(description='Shipping price of the shipping method.')
    minimum_order_price = Decimal(
        description='Minimum order price to use this shipping method',
        required=False)
    maximum_order_price = Decimal(
        description='Maximum order price to use this shipping method',
        required=False)
    minimum_order_weight = WeightScalar(
        description='Minimum order weight to use this shipping method',
        required=False)
    maximum_order_weight = WeightScalar(
        description='Maximum order weight to use this shipping method',
        required=False)
    type = ShippingMethodTypeEnum(
        description='Shipping type: price or weight based.')
    shipping_zone = graphene.ID(
        description='Shipping zone this method belongs to.',
        name='shippingZone')


class ShippingZoneInput(graphene.InputObjectType):
    name = graphene.String(
        description='Shipping zone\'s name. Visible only to the staff.')
    countries = graphene.List(
        graphene.String,
        description='List of countries in this shipping zone.')
    default = graphene.Boolean(
        description=dedent("""
            Is default shipping zone, that will be used
            for countries not covered by other zones."""))


class ShippingZoneMixin:

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        default = cleaned_input.get('default')
        if default is not None:
            if default_shipping_zone_exists(instance.pk):
                cls.add_error(
                    errors, 'default', 'Default shipping zone already exists.')
            elif cleaned_input.get('countries'):
                cleaned_input['countries'] = []
        else:
            cleaned_input['default'] = False
        return cleaned_input


class ShippingZoneCreate(ShippingZoneMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone, description='Created shipping zone.')

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


class ShippingZoneUpdate(ShippingZoneMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone, description='Updated shipping zone.')

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


class ShippingPriceMixin:

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        type = cleaned_input.get('type')
        if not type:
            return cleaned_input

        if type == ShippingMethodTypeEnum.PRICE.value:
            min_price = cleaned_input.get('minimum_order_price')
            max_price = cleaned_input.get('maximum_order_price')
            if min_price is None:
                cls.add_error(
                    errors, 'minimum_order_price',
                    'Minimum order price is required'
                    ' for Price Based shipping.')
            elif max_price is not None and max_price <= min_price:
                cls.add_error(
                    errors, 'maximum_order_price',
                    'Maximum order price should be larger than the minimum.')
        else:
            min_weight = cleaned_input.get('minimum_order_weight')
            max_weight = cleaned_input.get('maximum_order_weight')
            if min_weight is None:
                cls.add_error(
                    errors, 'minimum_order_weight',
                    'Minimum order weight is required for'
                    ' Weight Based shipping.')
            elif max_weight is not None and max_weight <= min_weight:
                cls.add_error(
                    errors, 'maximum_order_weight',
                    'Maximum order weight should be larger than the minimum.')
        return cleaned_input


class ShippingPriceCreate(ShippingPriceMixin, ModelMutation):
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


class ShippingPriceUpdate(ShippingPriceMixin, ModelMutation):
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
