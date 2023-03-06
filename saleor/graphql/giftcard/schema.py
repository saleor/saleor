import graphene
from graphql.error import GraphQLError

from ...core.permissions import GiftcardPermissions
from ...giftcard import models
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_31, PREVIEW_FEATURE
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.types import NonNullList
from ..core.utils import from_global_id_or_error
from .bulk_mutations import (
    GiftCardBulkActivate,
    GiftCardBulkCreate,
    GiftCardBulkDeactivate,
    GiftCardBulkDelete,
)
from .filters import GiftCardFilterInput, GiftCardTagFilterInput
from .mutations import (
    GiftCardActivate,
    GiftCardAddNote,
    GiftCardCreate,
    GiftCardDeactivate,
    GiftCardDelete,
    GiftCardResend,
    GiftCardUpdate,
)
from .resolvers import resolve_gift_card, resolve_gift_card_tags, resolve_gift_cards
from .sorters import GiftCardSortingInput
from .types import GiftCard, GiftCardCountableConnection, GiftCardTagCountableConnection


class GiftCardQueries(graphene.ObjectType):
    gift_card = PermissionsField(
        GiftCard,
        id=graphene.Argument(
            graphene.ID, description="ID of the gift card.", required=True
        ),
        description="Look up a gift card by ID.",
        permissions=[
            GiftcardPermissions.MANAGE_GIFT_CARD,
        ],
    )
    gift_cards = FilterConnectionField(
        GiftCardCountableConnection,
        sort_by=GiftCardSortingInput(
            description="Sort gift cards." + ADDED_IN_31 + PREVIEW_FEATURE
        ),
        filter=GiftCardFilterInput(
            description=(
                "Filtering options for gift cards." + ADDED_IN_31 + PREVIEW_FEATURE
            )
        ),
        description="List of gift cards.",
        permissions=[
            GiftcardPermissions.MANAGE_GIFT_CARD,
        ],
    )
    gift_card_currencies = PermissionsField(
        NonNullList(graphene.String),
        description="List of gift card currencies." + ADDED_IN_31 + PREVIEW_FEATURE,
        required=True,
        permissions=[
            GiftcardPermissions.MANAGE_GIFT_CARD,
        ],
    )
    gift_card_tags = FilterConnectionField(
        GiftCardTagCountableConnection,
        filter=GiftCardTagFilterInput(
            description="Filtering options for gift card tags."
        ),
        description="List of gift card tags." + ADDED_IN_31 + PREVIEW_FEATURE,
        permissions=[
            GiftcardPermissions.MANAGE_GIFT_CARD,
        ],
    )

    @staticmethod
    def resolve_gift_card(_root, _info: ResolveInfo, /, *, id: str):
        _, id = from_global_id_or_error(id, GiftCard)
        return resolve_gift_card(id)

    @staticmethod
    def resolve_gift_cards(
        _root, info: ResolveInfo, /, *, sort_by=None, filter=None, **kwargs
    ):
        sorting_by_balance = sort_by and "current_balance_amount" in sort_by.get(
            "field", []
        )
        filtering_by_currency = filter and "currency" in filter
        if sorting_by_balance and not filtering_by_currency:
            raise GraphQLError("Sorting by balance requires filtering by currency.")
        qs = resolve_gift_cards()
        qs = filter_connection_queryset(
            qs, {"sort_by": sort_by, "filter": filter, **kwargs}
        )
        return create_connection_slice(
            qs,
            info,
            {"sort_by": sort_by, "filter": filter, **kwargs},
            GiftCardCountableConnection,
        )

    @staticmethod
    def resolve_gift_card_currencies(_root, _info: ResolveInfo):
        return set(models.GiftCard.objects.values_list("currency", flat=True))

    @staticmethod
    def resolve_gift_card_tags(_root, info: ResolveInfo, **data):
        qs = resolve_gift_card_tags()
        qs = filter_connection_queryset(qs, data)
        return create_connection_slice(qs, info, data, GiftCardTagCountableConnection)


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
