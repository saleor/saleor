import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ...channel.types import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ShippingMethodType, ShippingZone
from .base import ShippingMethodTypeMixin, ShippingPriceMixin
from .shipping_price_create import ShippingPriceInput


class ShippingPriceUpdate(ShippingPriceMixin, ShippingMethodTypeMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )
    shipping_method = graphene.Field(
        ShippingMethodType, description="A shipping method."
    )

    class Arguments:
        id = graphene.ID(description="ID of a shipping price to update.", required=True)
        input = ShippingPriceInput(
            description="Fields required to update a shipping price.", required=True
        )

    class Meta:
        description = "Updates a new shipping price."
        model = models.ShippingMethod
        object_type = ShippingMethodType
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, _cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_price_updated, instance)

    @classmethod
    def success_response(cls, instance):
        shipping_method = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(shipping_method)

        response.shipping_zone = ChannelContext(
            node=instance.shipping_zone, channel_slug=None
        )
        return response
