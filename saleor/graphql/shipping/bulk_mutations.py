import graphene

from ...permission.enums import ShippingPermissions
from ...shipping import models
from ..core import ResolveInfo
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types import NonNullList, ShippingError
from ..plugins.dataloaders import get_plugin_manager_promise
from .types import ShippingMethod, ShippingZone


class ShippingZoneBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of shipping zone IDs to delete.",
        )

    class Meta:
        description = "Deletes shipping zones."
        model = models.ShippingZone
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        zones = [zone for zone in queryset]
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for zone in zones:
            manager.shipping_zone_deleted(zone)


class ShippingPriceBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of shipping price IDs to delete.",
        )

    class Meta:
        description = "Deletes shipping prices."
        model = models.ShippingMethod
        object_type = ShippingMethod
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def get_nodes_or_error(
        cls,
        ids,
        field,
        only_type=None,
        qs=None,
        schema=None,
    ):
        return super().get_nodes_or_error(
            ids,
            field,
            "ShippingMethodType",
            qs=models.ShippingMethod.objects,
            schema=schema,
        )

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        shipping_methods = [sm for sm in queryset]
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for method in shipping_methods:
            manager.shipping_price_deleted(method)
