from decimal import Decimal
from typing import Annotated
from uuid import uuid4

import pydantic
from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q
from django.utils import timezone

from ..checkout.models import Checkout
from ..core.prices import quantize_price
from ..graphql.payment.mutations.transaction.utils import (
    create_transaction_event_requested,
)
from ..order.models import Order
from ..payment import TransactionAction, TransactionEventType
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
    """Initialize session for gift card payment method.

    Attach payment method app identifier to the transaction, validate transaction data and gift card.

    Since gift card funds can be authorized to only one checkout at the time this function also detaches
    gift card from any checkouts it has been previously attached to.
    """
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
                "actions": [TransactionAction.CANCEL.upper()],
            },
        )
    finally:
        detach_gift_card_from_previous_checkout_transactions(gift_card)
        attach_gift_card_to_transaction(transaction_session_data, gift_card)


def attach_app_identifier_to_transaction(
    transaction_session_data: "TransactionSessionData",
):
    """Attach gift card payment gateway identifier to a transaction."""
    transaction_session_data.transaction.app_identifier = GIFT_CARD_PAYMENT_GATEWAY_ID
    transaction_session_data.transaction.save(update_fields=["app_identifier"])


def validate_transaction_session_data(
    transaction_session_data: "TransactionSessionData",
    source_object: Checkout | Order,
):
    """Validate whether object that the gift card is being attached to is a checkout and validate whether transaction data is correct."""
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
    """Check for the existence of given gift card and lock it for use in a database transaction. Check whether gift card has enough funds to cover transaction amount."""
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
    """Attach gift card to a transaction."""
    if not gift_card:
        return

    transaction_session_data.transaction.gift_card = gift_card
    transaction_session_data.transaction.save(update_fields=["gift_card"])


def detach_gift_card_from_previous_checkout_transactions(
    gift_card: GiftCard | None,
):
    """Find all gift card payment gateway transactions tied to a checkout and perform authorization cancellation for the same amount as authorization was granted.

    The function is used to ensure a single gift card does not authorize funds to more than a single checkout at the time.
    """
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
        request_event = create_transaction_event_requested(
            transaction_item,
            transaction_item.amount_authorized.amount,
            TransactionAction.CANCEL,
            app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        )

        response: dict[str, str | Decimal | list | None] = {
            "result": TransactionEventType.CANCEL_SUCCESS.upper(),
            "pspReference": str(uuid4()),
            "amount": transaction_item.amount_authorized.amount,
            "message": f"Gift card (code ending with: {gift_card.display_code}) has been authorized as payment method in a different checkout or has been authorized in the same checkout again.",
            "actions": [],
        }

        create_transaction_event_from_request_and_webhook_response(
            request_event,
            None,
            transaction_webhook_response=response,
        )

    transactions_to_cancel_qs.update(gift_card=None)


def charge_gift_card_transactions(
    order: "Order",
):
    """Find all gift card payment gateway transactions tied to an order and attempt to charge funds from gift cards.

    If gift card cannot be found or has insufficient funds the charge request fails.
    """

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
        request_event = create_transaction_event_requested(
            gift_card_transaction,
            gift_card_transaction.amount_authorized.amount,
            TransactionAction.CHARGE,
            app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        )

        response = {
            "result": TransactionEventType.CHARGE_FAILURE.upper(),
            "pspReference": str(uuid4()),
            "amount": gift_card_transaction.amount_authorized.amount,
            "message": "Gift card could not be found.",
        }

        if not gift_card_transaction.gift_card_id:
            create_transaction_event_from_request_and_webhook_response(
                request_event,
                None,
                transaction_webhook_response=response,
            )
            continue

        try:
            with transaction.atomic():
                gift_card = (
                    GiftCard.objects.filter(id=gift_card_transaction.gift_card_id)
                    .select_for_update()
                    .get()
                )

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
                    response["message"] = (
                        f"Gift card (ending: {gift_card.display_code})."
                    )
                    response["actions"] = [TransactionAction.REFUND.upper()]
        except GiftCard.DoesNotExist:
            # Gift card must have been just deleted.
            # Eat the exception, failure response dict is already prepared.
            pass

        create_transaction_event_from_request_and_webhook_response(
            request_event,
            None,
            transaction_webhook_response=response,
        )


def cancel_gift_card_transaction(
    transaction_item: "TransactionItem", request_event: "TransactionEvent"
):
    """Perform authorization cancellation for the same amount as authorization was granted.

    If checkout no longer exists or CANCEL action is not available for the transaction authorization cancellation fails.
    """
    response: dict[str, str | Decimal | list | None]
    amount = request_event.amount_value

    if (
        not transaction_item.checkout
        or TransactionAction.CANCEL not in transaction_item.available_actions
    ):
        response = {
            "result": TransactionEventType.CANCEL_FAILURE.upper(),
            "pspReference": str(uuid4()),
            "amount": amount,
        }
    else:
        response = {
            "result": TransactionEventType.CANCEL_SUCCESS.upper(),
            "pspReference": str(uuid4()),
            "amount": amount,
        }

        if amount >= transaction_item.authorized_value:
            response["actions"] = []

    create_transaction_event_from_request_and_webhook_response(
        request_event,
        None,
        transaction_webhook_response=response,
    )


def refund_gift_card_transaction(
    transaction_item: "TransactionItem", request_event: "TransactionEvent"
):
    """Refund funds to a gift card which previously were charged from the same gift card.

    If gift card no longer exists refund fails.
    """
    amount = request_event.amount_value

    response: dict[str, str | Decimal | list | None] = {
        "result": TransactionEventType.REFUND_FAILURE.upper(),
        "pspReference": str(uuid4()),
        "amount": amount,
        "message": "Gift card could not be found.",
    }

    if not transaction_item.gift_card_id:
        create_transaction_event_from_request_and_webhook_response(
            request_event,
            None,
            transaction_webhook_response=response,
        )
        return

    try:
        with transaction.atomic():
            gift_card = (
                GiftCard.objects.filter(id=transaction_item.gift_card_id)
                .select_for_update()
                .get()
            )
            gift_card.current_balance_amount = F("current_balance_amount") + amount
            gift_card.save(update_fields=["current_balance_amount"])
    except GiftCard.DoesNotExist:
        # Gift card must have been just deleted.
        # Eat the exception, failure response dict is already prepared.
        pass
    else:
        response = {
            "result": TransactionEventType.REFUND_SUCCESS.upper(),
            "pspReference": str(uuid4()),
            "amount": amount,
        }

        if amount >= transaction_item.charged_value:
            response["actions"] = []

    create_transaction_event_from_request_and_webhook_response(
        request_event,
        None,
        transaction_webhook_response=response,
    )
