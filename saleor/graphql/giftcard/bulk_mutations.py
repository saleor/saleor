import graphene

from ...core.permissions import GiftcardPermissions
from ...core.tracing import traced_atomic_transaction
from ...giftcard import events, models
from ..core.descriptions import ADDED_IN_31
from ..core.mutations import BaseBulkMutation, ModelBulkDeleteMutation
from ..core.types.common import GiftCardError


class GiftCardBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of gift card IDs to delete."
        )

    class Meta:
        description = f"{ADDED_IN_31} Delete gift cards."
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError


class GiftCardBulkActivate(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of gift card IDs to activate."
        )

    class Meta:
        description = f"{ADDED_IN_31} Activate gift cards."
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    @traced_atomic_transaction()
    def bulk_action(cls, info, queryset):
        queryset = queryset.filter(is_active=False)
        gift_card_ids = [gift_card.id for gift_card in queryset]
        queryset.update(is_active=True)
        events.gift_cards_activated_event(
            gift_card_ids, user=info.context.user, app=info.context.app
        )


class GiftCardBulkDeactivate(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of gift card IDs to deactivate.",
        )

    class Meta:
        description = f"{ADDED_IN_31} Deactivate gift cards."
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    @traced_atomic_transaction()
    def bulk_action(cls, info, queryset):
        queryset = queryset.filter(is_active=True)
        gift_card_ids = [gift_card.id for gift_card in queryset]
        queryset.update(is_active=False)
        events.gift_cards_deactivated_event(
            gift_card_ids, user=info.context.user, app=info.context.app
        )
