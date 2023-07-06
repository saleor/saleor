import graphene

from ....giftcard import events
from ....giftcard.utils import deactivate_gift_card
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardDeactivate(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="Deactivated gift card.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a gift card to deactivate.")

    class Meta:
        description = "Deactivate a gift card."
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED,
                description="A gift card was deactivated.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        gift_card = cls.get_node_or_error(
            info, id, field="gift_card_id", only_type=GiftCard
        )
        # create event only when is_active value has changed
        create_event = gift_card.is_active
        deactivate_gift_card(gift_card)
        if create_event:
            app = get_app_promise(info.context).get()
            events.gift_card_deactivated_event(
                gift_card=gift_card,
                user=info.context.user,
                app=app,
            )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.gift_card_status_changed, gift_card)
        return GiftCardDeactivate(gift_card=gift_card)
