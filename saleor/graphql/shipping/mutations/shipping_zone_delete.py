import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ...channel.types import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ShippingZone


class ShippingZoneDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping zone to delete.")

    class Meta:
        description = "Deletes a shipping zone."
        model = models.ShippingZone
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, _cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_zone_deleted, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response
