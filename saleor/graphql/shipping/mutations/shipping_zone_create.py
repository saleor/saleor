import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.doc_category import DOC_CATEGORY_SHIPPING
from ...core.mutations import DeprecatedModelMutation
from ...core.types import BaseInputObjectType, NonNullList, ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ShippingZone
from .base import ShippingZoneMixin


class ShippingZoneCreateInput(BaseInputObjectType):
    name = graphene.String(
        description="Shipping zone's name. Visible only to the staff."
    )
    description = graphene.String(description="Description of the shipping zone.")
    countries = NonNullList(
        graphene.String, description="List of countries in this shipping zone."
    )
    default = graphene.Boolean(
        description=(
            "Default shipping zone will be used for countries not covered by other "
            "zones."
        )
    )
    add_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to assign to a shipping zone",
    )
    add_channels = NonNullList(
        graphene.ID,
        description="List of channels to assign to the shipping zone.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingZoneCreate(ShippingZoneMixin, DeprecatedModelMutation):
    class Arguments:
        input = ShippingZoneCreateInput(
            description="Fields required to create a shipping zone.", required=True
        )

    class Meta:
        description = "Creates a new shipping zone."
        model = models.ShippingZone
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, _cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_zone_created, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response
