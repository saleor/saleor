import graphene

from ...core.permissions import GiftcardPermissions
from ..core.descriptions import ADDED_IN_31
from ..core.fields import FilterInputConnectionField
from ..core.utils import from_global_id_or_error
from ..decorators import permission_required
from .filters import GiftCardFilterInput
from .mutations import (
    GiftCardActivate,
    GiftCardCreate,
    GiftCardDeactivate,
    GiftCardDelete,
    GiftCardUpdate,
)
from .resolvers import resolve_gift_card, resolve_gift_cards
from .types import GiftCard


class GiftCardQueries(graphene.ObjectType):
    gift_card = graphene.Field(
        GiftCard,
        id=graphene.Argument(
            graphene.ID, description="ID of the gift card.", required=True
        ),
        description="Look up a gift card by ID.",
    )
    gift_cards = FilterInputConnectionField(
        GiftCard,
        filter=GiftCardFilterInput(
            description=f"{ADDED_IN_31} Filtering options for gift cards."
        ),
        description="List of gift cards.",
    )

    @permission_required(GiftcardPermissions.MANAGE_GIFT_CARD)
    def resolve_gift_card(self, info, **data):
        _, id = from_global_id_or_error(data.get("id"), GiftCard)
        return resolve_gift_card(id)

    @permission_required(GiftcardPermissions.MANAGE_GIFT_CARD)
    def resolve_gift_cards(self, info, **_kwargs):
        return resolve_gift_cards()


class GiftCardMutations(graphene.ObjectType):
    gift_card_activate = GiftCardActivate.Field()
    gift_card_create = GiftCardCreate.Field()
    gift_card_delete = GiftCardDelete.Field()
    gift_card_deactivate = GiftCardDeactivate.Field()
    gift_card_update = GiftCardUpdate.Field()
