import graphene

from ....core.tracing import traced_atomic_transaction
from ....giftcard import events, models
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.mutations import BaseBulkMutation
from ...core.types import GiftCardError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardBulkDeactivate(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of gift card IDs to deactivate.",
        )

    class Meta:
        description = "Deactivate gift cards." + ADDED_IN_31
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED,
                description="A gift card was deactivated.",
            )
        ]

    @classmethod
    @traced_atomic_transaction()
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        app = get_app_promise(info.context).get()
        queryset = queryset.filter(is_active=True)
        gift_card_ids = [gift_card.id for gift_card in queryset]
        queryset.update(is_active=False)
        events.gift_cards_deactivated_event(
            gift_card_ids, user=info.context.user, app=app
        )
        webhooks = get_webhooks_for_event(
            WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED
        )
        manager = get_plugin_manager_promise(info.context).get()
        for card in models.GiftCard.objects.filter(id__in=gift_card_ids):
            cls.call_event(manager.gift_card_status_changed, card, webhooks=webhooks)
