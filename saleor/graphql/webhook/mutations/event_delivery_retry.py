import graphene

from ....permission.enums import AppPermission
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.types import WebhookError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import EventDelivery


class EventDeliveryRetry(BaseMutation):
    delivery = graphene.Field(EventDelivery, description="Event delivery.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the event delivery to retry."
        )

    class Meta:
        description = "Retries event delivery."
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookError

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, **data):
        delivery = cls.get_node_or_error(
            info,
            data["id"],
            only_type=EventDelivery,
        )
        manager = get_plugin_manager_promise(info.context).get()
        manager.event_delivery_retry(delivery)
        return EventDeliveryRetry(delivery=delivery)
