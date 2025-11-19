from decimal import Decimal
from typing import Annotated
from uuid import uuid4

import pydantic
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
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


class GiftCardPaymentGatewayException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Gift card payment gateway error"
        super().__init__(msg)


def transaction_initialize_session_with_gift_card_payment_method(
    transaction_session_data: "TransactionSessionData",
    source_object: Checkout | Order,
) -> "TransactionSessionResult":
    attach_app_identifier_to_transaction(transaction_session_data)
    gift_card = None

    try:
        validate_transaction_session_data(transaction_session_data, source_object)
        gift_card = validate_and_get_gift_card(transaction_session_data)
    except GiftCardPaymentGatewayException as exc:
        return TransactionSessionResult(
            app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
            response={
                "result": TransactionEventType.AUTHORIZATION_FAILURE.upper(),
                "pspReference": str(uuid4()),
                "amount": transaction_session_data.action.amount,
                "message": exc,
            },
        )
    else:
        return TransactionSessionResult(
            app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
            response={
                "result": TransactionEventType.AUTHORIZATION_SUCCESS.upper(),
                "pspReference": str(uuid4()),
                "amount": transaction_session_data.action.amount,
                "message": f"Gift card (ending: {gift_card.display_code}).",
            },
        )
    finally:
        detach_gift_card_from_previous_checkout_transactions(gift_card)
        attach_gift_card_to_transaction(transaction_session_data, gift_card)


def attach_app_identifier_to_transaction(
    transaction_session_data: "TransactionSessionData",
):
    transaction_session_data.transaction.app_identifier = GIFT_CARD_PAYMENT_GATEWAY_ID
    transaction_session_data.transaction.save(update_fields=["app_identifier"])


def validate_transaction_session_data(
    transaction_session_data: "TransactionSessionData",
    source_object: Checkout | Order,
):
    if not isinstance(source_object, Checkout):
        raise GiftCardPaymentGatewayException(
            msg=f"Cannot initialize transaction for payment gateway: {GIFT_CARD_PAYMENT_GATEWAY_ID} and object type other than Checkout."
        )

    try:
        GiftCardPaymentGatewayDataSchema.model_validate(
            transaction_session_data.payment_gateway_data.data
        )
    except pydantic.ValidationError as exc:
        raise GiftCardPaymentGatewayException(
            msg="Incorrect payment gateway data."
        ) from exc


def validate_and_get_gift_card(
    transaction_session_data: "TransactionSessionData",
):
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
    except GiftCard.DoesNotExist as exc:
        raise GiftCardPaymentGatewayException(
            msg="Gift card code is not valid."
        ) from exc

    # Check whether gift card has enough funds to cover the amount.
    if transaction_session_data.action.amount > gift_card.current_balance_amount:
        raise GiftCardPaymentGatewayException(
            msg=f"Gift card has insufficient amount ({quantize_price(gift_card.current_balance_amount, gift_card.currency)}) "
            f"to cover requested amount ({quantize_price(transaction_session_data.action.amount, transaction_session_data.action.currency)})."
        )

    return gift_card


def attach_gift_card_to_transaction(
    transaction_session_data: "TransactionSessionData",
    gift_card: GiftCard | None,
):
    if not gift_card:
        return

    transaction_session_data.transaction.gift_card = gift_card
    transaction_session_data.transaction.save(update_fields=["gift_card"])


def detach_gift_card_from_previous_checkout_transactions(
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
        # must cancel transactions where checkout identifier is not empty
        Q(checkout_id__isnull=False),
        # must cancel transactions where order identifier is empty (transaction is not
        # tied to an order yet)
        Q(order_id__isnull=True),
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
            message=f"Gift card (code ending with: {gift_card.display_code}) has been authorized as payment method in a different checkout or has been authorized in the same checkout again.",
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


def charge_gift_card_transactions(
    order: "Order",
):
    # Order object may already have prefetched related objects.
    # Prefetched payment transactions cause logic called a few layers beneath to operate on outdated
    # order transactions therfore here the cache is dropped.
    if hasattr(order, "_prefetched_objects_cache"):
        order._prefetched_objects_cache.pop("payment_transactions", None)

    # Ensure that gift card transaction is not attempted to be charged more than once.
    gift_card_transactions = order.payment_transactions.filter(
        ~Exists(
            TransactionEvent.objects.filter(
                transaction=OuterRef("pk"), type=TransactionEventType.CHARGE_REQUEST
            )
        ),
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        gift_card__isnull=False,
        authorized_value__gt=Decimal(0),
        charged_value=Decimal(0),
    )

    for gift_card_transaction in gift_card_transactions:
        with transaction.atomic():
            gift_card = (
                GiftCard.objects.filter(id=gift_card_transaction.gift_card_id)  # type: ignore[misc]
                .select_for_update()
                .get()
            )
            transaction_event, _ = TransactionEvent.objects.get_or_create(
                app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
                transaction=gift_card_transaction,
                type=TransactionEventType.CHARGE_REQUEST,
                currency=gift_card_transaction.currency,
                amount_value=gift_card_transaction.amount_authorized.amount,
                defaults={
                    "include_in_calculations": False,
                    "currency": gift_card_transaction.currency,
                    "amount_value": gift_card_transaction.amount_authorized.amount,
                },
            )

            response = {
                "result": TransactionEventType.CHARGE_FAILURE.upper(),
                "pspReference": gift_card_transaction.psp_reference,
                "amount": gift_card_transaction.amount_authorized.amount,
            }

            if (
                gift_card_transaction.authorized_value
                > gift_card.current_balance_amount
            ):
                response["message"] = (
                    f"Gift card has insufficient amount ({quantize_price(gift_card.current_balance_amount, gift_card.currency)}) "
                    f"to cover requested amount ({quantize_price(gift_card_transaction.authorized_value, gift_card_transaction.currency)})."
                )
            else:
                gift_card.current_balance_amount -= (
                    gift_card_transaction.authorized_value
                )
                gift_card.save(update_fields=["current_balance_amount"])
                response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
                response["message"] = f"Gift card (ending: {gift_card.display_code})."

            create_transaction_event_from_request_and_webhook_response(
                transaction_event,
                None,
                transaction_webhook_response=response,
            )
