import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from ....app.models import App
from ....core import models
from ....permission.enums import AppPermission
from ....webhook.error_codes import WebhookErrorCode
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_WEBHOOKS
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
        doc_category = DOC_CATEGORY_WEBHOOKS
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookError

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, **data):
        apps = App.objects.filter(removed_at__isnull=True).values("pk")
        webhook = Webhook.objects.filter(
            Exists(apps.filter(id=OuterRef("app_id")))
        ).values("pk")
        deliveries = models.EventDelivery.objects.filter(
            Exists(webhook.filter(id=OuterRef("webhook_id")))
        )

        delivery = cls.get_node_or_error(
            info,
            data["id"],
            only_type=EventDelivery,
            qs=deliveries,
        )
        if delivery.event_type == WebhookEventAsyncType.SALEOR_API_URL_CHANGED:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Deliveries of the SALEOR_API_URL_CHANGED event can't be "
                        "retried, because a retry would carry the new Saleor API URL "
                        "instead of the previous one. Reinstall the app instead.",
                        code=WebhookErrorCode.INVALID.value,
                    )
                }
            )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.event_delivery_retry, delivery)
        return EventDeliveryRetry(delivery=delivery)
