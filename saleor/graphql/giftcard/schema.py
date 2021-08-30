import graphene
from graphql.error import GraphQLError

from ...core.permissions import GiftcardPermissions
from ...giftcard import models
from ..core.descriptions import ADDED_IN_31
from ..core.fields import FilterInputConnectionField
from ..core.utils import from_global_id_or_error
from ..decorators import permission_required
from .bulk_mutations import (
    GiftCardBulkActivate,
    GiftCardBulkCreate,
    GiftCardBulkDeactivate,
    GiftCardBulkDelete,
)
from .filters import GiftCardFilterInput
from .mutations import (
    GiftCardActivate,
    GiftCardAddNote,
    GiftCardCreate,
    GiftCardDeactivate,
    GiftCardDelete,
    GiftCardResend,
    GiftCardUpdate,
)
from .resolvers import resolve_gift_card, resolve_gift_cards
from .sorters import GiftCardSortingInput
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
        sort_by=GiftCardSortingInput(description=f"{ADDED_IN_31} Sort gift cards."),
        filter=GiftCardFilterInput(
            description=f"{ADDED_IN_31} Filtering options for gift cards."
        ),
        description="List of gift cards.",
    )
    gift_card_currencies = graphene.Field(
        graphene.List(graphene.NonNull(graphene.String)),
        description=f"{ADDED_IN_31} List of gift card currencies.",
        required=True,
    )

    @permission_required(GiftcardPermissions.MANAGE_GIFT_CARD)
    def resolve_gift_card(self, info, **data):
        _, id = from_global_id_or_error(data.get("id"), GiftCard)
        return resolve_gift_card(id)

    @permission_required(GiftcardPermissions.MANAGE_GIFT_CARD)
    def resolve_gift_cards(self, info, **data):
        sorting_by_balance = "sort_by" in data and "current_balance_amount" in data[
            "sort_by"
        ].get("field", [])
        filtering_by_currency = "filter" in data and "currency" in data["filter"]
        if sorting_by_balance and not filtering_by_currency:
            raise GraphQLError("Sorting by balance requires filtering by currency.")
        return resolve_gift_cards()

    @permission_required(GiftcardPermissions.MANAGE_GIFT_CARD)
    def resolve_gift_card_currencies(self, info, **data):
        return set(models.GiftCard.objects.values_list("currency", flat=True))


class GiftCardMutations(graphene.ObjectType):
    gift_card_activate = GiftCardActivate.Field()
    gift_card_create = GiftCardCreate.Field()
    gift_card_delete = GiftCardDelete.Field()
    gift_card_deactivate = GiftCardDeactivate.Field()
    gift_card_update = GiftCardUpdate.Field()
    gift_card_resend = GiftCardResend.Field()
    gift_card_add_note = GiftCardAddNote.Field()

    gift_card_bulk_create = GiftCardBulkCreate.Field()
    gift_card_bulk_delete = GiftCardBulkDelete.Field()
    gift_card_bulk_activate = GiftCardBulkActivate.Field()
    gift_card_bulk_deactivate = GiftCardBulkDeactivate.Field()
