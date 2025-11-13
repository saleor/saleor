from typing import Annotated
from uuid import uuid4

import pydantic
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..graphql.channel.types import TransactionFlowStrategyEnum
from ..payment import TransactionEventType
from ..payment.error_codes import TransactionInitializeErrorCode
from ..payment.interface import (
    PaymentGatewayData,
    TransactionSessionData,
    TransactionSessionResult,
)
from ..payment.models import TransactionEvent, TransactionItem
from ..plugins.manager import PluginsManager
from .const import GIFT_CARD_PAYMENT_GATEWAY_ID
from .models import GiftCard


class GiftCardPaymentGatewayDataSchema(pydantic.BaseModel):
    code: Annotated[
        str,
        pydantic.Field(
            description="Gift card code.",
            min_length=8,
            max_length=16,
        ),
    ]


def clean_gift_card_payment_gateway_data(payment_gateway: PaymentGatewayData) -> None:
    try:
        GiftCardPaymentGatewayDataSchema.model_validate(payment_gateway.data)
    except pydantic.ValidationError as exc:
        raise ValidationError(
            {
                "payment_gateway": ValidationError(
                    message=f"Invalid data for {payment_gateway.app_identifier} payment gateway.",
                    code=TransactionInitializeErrorCode.INVALID.value,
                )
            }
        ) from exc


def clean_action_for_gift_card_payment_gateway(
    action: str | None,
) -> str:
    if action is None or action == TransactionFlowStrategyEnum.AUTHORIZATION.value:
        return TransactionFlowStrategyEnum.AUTHORIZATION.value

    raise ValidationError(
        {
            "action": ValidationError(
                message=f"Invalid action for {GIFT_CARD_PAYMENT_GATEWAY_ID} payment gateway.",
                code=TransactionInitializeErrorCode.INVALID.value,
            )
        }
    )


def transaction_initialize_session_with_gift_card_payment_method(
    transaction_session_data: "TransactionSessionData",
) -> tuple["TransactionSessionResult", GiftCard | None]:
    transaction_session_result = TransactionSessionResult(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        response={
            "result": TransactionEventType.AUTHORIZATION_FAILURE.upper(),
            "pspReference": str(uuid4()),
            "amount": transaction_session_data.action.amount,
        },
    )

    # Check for existence of an active gift card and validate currency.
    try:
        gift_card = (
            GiftCard.objects.filter(
                code=transaction_session_data.payment_gateway_data.data["code"],  # type: ignore[call-overload, index]
                currency=transaction_session_data.action.currency,
                is_active=True,
            )
            .select_for_update()
            .get()
        )
    except GiftCard.DoesNotExist:
        return transaction_session_result, None

    # Check whether gift card has enough funds to cover the amount.
    if transaction_session_data.action.amount > gift_card.current_balance_amount:
        return transaction_session_result, None

    transaction_session_result.response["result"] = (  # type: ignore[index]
        TransactionEventType.AUTHORIZATION_SUCCESS.upper()
    )

    return transaction_session_result, gift_card


def attach_gift_card_to_transaction(
    transaction_session_data: "TransactionSessionData",
    gift_card: GiftCard | None,
):
    if not gift_card:
        return

    transaction_session_data.transaction.gift_card = gift_card
    transaction_session_data.transaction.save(update_fields=["gift_card"])


def detach_gift_card_from_previous_checkout_transactions(
    transaction_session_data: "TransactionSessionData",
    gift_card: GiftCard | None,
    manager: "PluginsManager",
):
    if not gift_card:
        return

    # Detach gift card from the previously attached transaction items and create authorization cancellation events.
    transactions_to_cancel_qs = TransactionItem.objects.filter(
        # must cancel transactions for gift card payment gateway
        Q(app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID),
        # must cancel transactions for this gift card
        Q(gift_card=gift_card),
        # must not cancel transactions for the source object
        ~Q(checkout=transaction_session_data.source_object)
        # must cancel transactions where checkout identifier is not empty
        & Q(checkout_id__isnull=False)
        # must cancel transactions where order identifier is empty (transaction is not
        # tied to an order yet)
        & Q(order_id__isnull=True),
    )

    for transaction_item in transactions_to_cancel_qs:
        response = {
            "result": TransactionEventType.CANCEL_SUCCESS.upper(),
            "pspReference": transaction_item.psp_reference,
            "amount": transaction_item.amount_authorized.amount,
        }

        transaction_event, _ = TransactionEvent.objects.get_or_create(
            transaction=transaction_item,
            type=TransactionEventType.CANCEL_REQUEST,
            currency=transaction_item.currency,
            amount_value=transaction_item.amount_authorized.amount,
            message=f"Gift card (code ending with: {gift_card.display_code}) has been authorized as payment method in a different checkout.",
            defaults={
                "include_in_calculations": False,
                "currency": transaction_item.currency,
                "amount_value": transaction_item.amount_authorized.amount,
            },
        )

        from ..payment.utils import create_transaction_event_for_transaction_session

        create_transaction_event_for_transaction_session(
            transaction_event,
            None,
            transaction_webhook_response=response,
            manager=manager,
        )

    transactions_to_cancel_qs.update(gift_card=None)
