import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ShippingZone


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
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.SHIPPING_ZONE_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for zone in zones:
            cls.call_event(manager.shipping_zone_deleted, zone, webhooks=webhooks)
