import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ShippingMethod


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
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.SHIPPING_PRICE_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for method in shipping_methods:
            cls.call_event(manager.shipping_price_deleted, method, webhooks=webhooks)
