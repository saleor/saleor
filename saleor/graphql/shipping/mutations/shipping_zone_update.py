import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ...channel.types import ChannelContext
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHIPPING
from ...core.mutations import ModelMutation
from ...core.types import NonNullList, ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ShippingZone
from .base import ShippingZoneMixin
from .shipping_zone_create import ShippingZoneCreateInput


class ShippingZoneUpdateInput(ShippingZoneCreateInput):
    remove_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to unassign from a shipping zone",
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels to unassign from the shipping zone.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingZoneUpdate(ShippingZoneMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of a shipping zone to update.", required=True)
        input = ShippingZoneUpdateInput(
            description="Fields required to update a shipping zone.", required=True
        )

    class Meta:
        description = "Updates a new shipping zone."
        model = models.ShippingZone
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, _cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_zone_updated, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response
