from typing import Annotated
from uuid import uuid4

import pydantic
from django.db.models import Q
from django.utils import timezone

from ..checkout.models import Checkout
from ..core.prices import quantize_price
from ..order.models import Order
from ..payment import TransactionEventType
from ..payment.interface import (
    TransactionSessionData,
    TransactionSessionResult,
)
from ..payment.models import TransactionEvent, TransactionItem
from ..payment.utils import (
    create_transaction_event_from_request_and_webhook_response,
)
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


def transaction_initialize_session_with_gift_card_payment_method(
    transaction_session_data: "TransactionSessionData",
    source_object: Checkout | Order,
) -> tuple["TransactionSessionResult", GiftCard | None]:
    transaction_session_result = TransactionSessionResult(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        response={
            "result": TransactionEventType.AUTHORIZATION_FAILURE.upper(),
            "pspReference": str(uuid4()),
            "amount": transaction_session_data.action.amount,
        },
    )

    if not isinstance(source_object, Checkout):
        transaction_session_result.response["message"] = (  # type: ignore[index]
            f"Cannot initialize transaction for payment gateway: {GIFT_CARD_PAYMENT_GATEWAY_ID} and object type other than Checkout."
        )
        return transaction_session_result, None

    try:
        GiftCardPaymentGatewayDataSchema.model_validate(
            transaction_session_data.payment_gateway_data.data
        )
    except pydantic.ValidationError:
        transaction_session_result.response["message"] = (  # type: ignore[index]
            "Incorrect payment gateway data."
        )
        return transaction_session_result, None

    # Check for existence of an active gift card and validate currency.
    try:
        gift_card = (
            GiftCard.objects.active(date=timezone.now().date())
            .filter(
                code=transaction_session_data.payment_gateway_data.data["code"],  # type: ignore[call-overload, index]
                currency=transaction_session_data.action.currency,
            )
            .select_for_update()
            .get()
        )
    except GiftCard.DoesNotExist:
        transaction_session_result.response["message"] = "Gift card code is not valid."  # type: ignore[index]
        return transaction_session_result, None

    # Check whether gift card has enough funds to cover the amount.
    if transaction_session_data.action.amount > gift_card.current_balance_amount:
        transaction_session_result.response["message"] = (  # type: ignore[index]
            f"Gift card has insufficient amount ({quantize_price(gift_card.current_balance_amount, gift_card.currency)}) "
            f"to cover requested amount ({quantize_price(transaction_session_data.action.amount, transaction_session_data.action.currency)})."
        )
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
            app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
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

        create_transaction_event_from_request_and_webhook_response(
            transaction_event,
            None,
            transaction_webhook_response=response,
        )

    transactions_to_cancel_qs.update(gift_card=None)
