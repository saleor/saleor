import graphene

from ....giftcard import models
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import GiftCardError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of gift card IDs to delete."
        )

    class Meta:
        description = "Delete gift cards." + ADDED_IN_31
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_DELETED,
                description="A gift card was deleted.",
            )
        ]

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        instances = [card for card in queryset]
        queryset.delete()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.GIFT_CARD_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for instance in instances:
            cls.call_event(manager.gift_card_deleted, instance, webhooks=webhooks)
