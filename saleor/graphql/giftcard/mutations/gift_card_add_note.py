import graphene
from django.core.exceptions import ValidationError

from ....giftcard import events
from ....giftcard.error_codes import GiftCardErrorCode
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import GiftCardError
from ...core.validators import validate_required_string_field
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard, GiftCardEvent


@doc(category=DOC_CATEGORY_GIFT_CARDS)
class GiftCardAddNoteInput(graphene.InputObjectType):
    message = graphene.String(description="Note message.", required=True)


@doc(category=DOC_CATEGORY_GIFT_CARDS)
@webhook_events(async_events={WebhookEventAsyncType.GIFT_CARD_UPDATED})
class GiftCardAddNote(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="Gift card with the note added.")
    event = graphene.Field(GiftCardEvent, description="Gift card note created.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the gift card to add a note for."
        )
        input = GiftCardAddNoteInput(
            required=True,
            description="Fields required to create a note for the gift card.",
        )

    class Meta:
        description = "Adds note to the gift card."
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    def clean_input(cls, _info: ResolveInfo, _instance, data):
        try:
            cleaned_input = validate_required_string_field(data, "message")
        except ValidationError as e:
            raise ValidationError(
                {
                    "message": ValidationError(
                        "Message can't be empty.",
                        code=GiftCardErrorCode.REQUIRED.value,
                    )
                }
            ) from e
        return cleaned_input

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        gift_card = cls.get_node_or_error(info, id, only_type=GiftCard)
        cleaned_input = cls.clean_input(info, gift_card, input)
        app = get_app_promise(info.context).get()
        event = events.gift_card_note_added_event(
            gift_card=gift_card,
            user=info.context.user,
            app=app,
            message=cleaned_input["message"],
        )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.gift_card_updated, gift_card)
        return GiftCardAddNote(gift_card=gift_card, event=event)
