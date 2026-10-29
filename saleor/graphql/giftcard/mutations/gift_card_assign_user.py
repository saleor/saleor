import graphene
from django.core.exceptions import ValidationError

from ....account.models import User as UserModel
from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....giftcard import events
from ....giftcard.error_codes import GiftCardErrorCode
from ....giftcard.utils import GiftCardCannotAssign, assign_gift_card_to_user
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...account.types import User
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardAssignUser(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="The assigned gift card.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the gift card.")
        user_id = graphene.ID(
            required=True,
            description="ID of the customer to restrict the card to.",
        )

    class Meta:
        description = (
            "Restrict a gift card so only the given customer can use it. "
            + ADDED_IN_323
        )
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
        cls, _root, info: ResolveInfo, /, *, id, user_id
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
        user = cls.get_node_or_error(
            info,
            user_id,
            only_type=User,
            field="user_id",
            qs=UserModel.objects.filter(is_active=True),
        )
        if user is None:
            raise ValidationError(
                {
                    "user_id": ValidationError(
                        "Couldn't resolve to a user.",
                        code=GiftCardErrorCode.NOT_FOUND.value,
                    )
                }
            )

        previous_user_id = gift_card.assigned_to_id
        previous_email = gift_card.assigned_to_email

        staff = info.context.user
        app = get_app_promise(info.context).get()

        try:
            with traced_atomic_transaction():
                assign_gift_card_to_user(gift_card, user)
                events.gift_card_assigned_event(
                    gift_card, previous_user_id, previous_email, staff, app
                )
        except GiftCardCannotAssign as e:
            raise ValidationError(
                {
                    "id": ValidationError(
                        str(e), code=GiftCardErrorCode.CANNOT_ASSIGN.value
                    )
                }
            ) from e

        manager = get_plugin_manager_promise(info.context).get()
        call_event(manager.gift_card_updated, gift_card)
        return cls(gift_card=gift_card, errors=[])
