from decimal import Decimal

import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....giftcard import events
from ....giftcard.error_codes import GiftCardErrorCode
from ....giftcard.lock_objects import gift_card_qs_select_for_update
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal as DecimalScalar
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardBalanceAdjust(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="The adjusted gift card.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the gift card to adjust.")
        amount = DecimalScalar(
            required=True,
            description=(
                "Signed amount to adjust the current balance by. Positive tops up, "
                "negative deducts. A deduction below zero clamps the balance to zero. "
                "A top-up above the initial balance raises the initial balance to the "
                "new current balance. " + ADDED_IN_323
            ),
        )

    class Meta:
        description = "Adjust a gift card's balance by a delta. " + ADDED_IN_323
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
        cls, _root, info: ResolveInfo, /, *, id, amount
    ):
        gift_card = cls.get_node_or_error(info, id, only_type=GiftCard, field="id")

        if amount == Decimal(0):
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Adjustment amount cannot be zero.",
                        code=GiftCardErrorCode.INVALID.value,
                    )
                }
            )
        try:
            validate_price_precision(abs(amount), gift_card.currency)
        except ValidationError as e:
            e.code = GiftCardErrorCode.INVALID.value
            raise ValidationError({"amount": e}) from e

        user = info.context.user
        app = get_app_promise(info.context).get()

        with traced_atomic_transaction():
            locked = gift_card_qs_select_for_update().get(pk=gift_card.pk)
            old_current = locked.current_balance_amount
            old_initial = locked.initial_balance_amount

            new_current = old_current + amount
            if new_current < Decimal(0):
                new_current = Decimal(0)
            locked.current_balance_amount = new_current
            update_fields = ["current_balance_amount"]
            if new_current > old_initial:
                locked.initial_balance_amount = new_current
                update_fields.append("initial_balance_amount")
            locked.save(update_fields=update_fields)

            events.gift_card_balance_adjusted_event(
                locked, old_current, old_initial, user, app
            )

        manager = get_plugin_manager_promise(info.context).get()
        call_event(manager.gift_card_updated, locked)

        return cls(gift_card=locked, errors=[])
