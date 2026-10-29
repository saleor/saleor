import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....giftcard import events
from ....giftcard.error_codes import GiftCardErrorCode
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardUnassignUser(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="The unassigned gift card.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the gift card.")

    class Meta:
        description = "Remove a customer restriction from a gift card. " + ADDED_IN_323
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_UPDATED,
                description="A gift card was updated.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id
    ):
        gift_card = cls.get_node_or_error(info, id, only_type=GiftCard, field="id")
        if gift_card is None:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Couldn't resolve to a gift card.",
                        code=GiftCardErrorCode.NOT_FOUND.value,
                    )
                }
            )
        previous_user_id = gift_card.assigned_to_id
        previous_email = gift_card.assigned_to_email

        staff = info.context.user
        app = get_app_promise(info.context).get()

        with traced_atomic_transaction():
            gift_card.assigned_to = None
            gift_card.assigned_to_email = None
            gift_card.save(update_fields=["assigned_to", "assigned_to_email"])
            events.gift_card_unassigned_event(
                gift_card, previous_user_id, previous_email, staff, app
            )

        manager = get_plugin_manager_promise(info.context).get()
        call_event(manager.gift_card_updated, gift_card)
        return cls(gift_card=gift_card, errors=[])
