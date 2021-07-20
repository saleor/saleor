import logging
from typing import Optional

from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from stripe.error import SignatureVerificationError
from stripe.stripe_object import StripeObject

from ....checkout.complete_checkout import complete_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....core.transactions import transaction_with_commit_on_errors
from ....discount.utils import fetch_active_discounts
from ....order.actions import order_captured, order_refunded, order_voided
from ....plugins.manager import get_plugins_manager
from ... import ChargeStatus, TransactionKind
from ...interface import GatewayConfig, GatewayResponse
from ...models import Payment
from ...utils import create_transaction, gateway_postprocess, price_from_minor_unit
from .consts import (
    WEBHOOK_AUTHORIZED_EVENT,
    WEBHOOK_CANCELED_EVENT,
    WEBHOOK_FAILED_EVENT,
    WEBHOOK_PROCESSING_EVENT,
    WEBHOOK_REFUND_EVENT,
    WEBHOOK_SUCCESS_EVENT,
)
from .stripe_api import construct_stripe_event

logger = logging.getLogger(__name__)


@transaction_with_commit_on_errors()
def handle_webhook(request: WSGIRequest, gateway_config: "GatewayConfig"):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    endpoint_secret = gateway_config.connection_params["webhook_secret"]
    api_key = gateway_config.connection_params["secret_api_key"]
    try:
        event = construct_stripe_event(
            api_key=api_key,
            payload=payload,
            sig_header=sig_header,
            endpoint_secret=endpoint_secret,
        )
    except ValueError as e:
        # Invalid payload
        logger.warning(
            "Received invalid payload for Stripe webhook", extra={"error": e}
        )
        return HttpResponse(status=400)
    except SignatureVerificationError as e:
        # Invalid signature
        logger.warning("Invalid signature for Stripe webhook", extra={"error": e})
        return HttpResponse(status=400)

    webhook_handlers = {
        WEBHOOK_SUCCESS_EVENT: handle_successful_payment_intent,
        WEBHOOK_AUTHORIZED_EVENT: handle_authorized_payment_intent,
        WEBHOOK_PROCESSING_EVENT: handle_processing_payment_intent,
        WEBHOOK_FAILED_EVENT: handle_failed_payment_intent,
        WEBHOOK_CANCELED_EVENT: handle_failed_payment_intent,
        WEBHOOK_REFUND_EVENT: handle_refund,
    }
    if event.type in webhook_handlers:
        logger.debug(
            "Processing new Stripe webhook",
            extra={"event_type": event.type, "event_id": event.id},
        )
        webhook_handlers[event.type](event.data.object, gateway_config)
    else:
        logger.warning(
            "Received unhandled webhook events", extra={"event_type": event.type}
        )
    return HttpResponse(status=200)


def _get_payment(payment_intent_id: str) -> Optional[Payment]:
    return (
        Payment.objects.prefetch_related(
            "checkout",
        )
        .select_for_update(of=("self",))
        .filter(transactions__token=payment_intent_id, is_active=True)
        .first()
    )


def _get_checkout(payment_id: int) -> Optional[Checkout]:
    return (
        Checkout.objects.prefetch_related("payments")
        .select_for_update(of=("self",))
        .filter(payments__id=payment_id, payments__is_active=True)
        .first()
    )


def _finalize_checkout(
    checkout: Checkout,
    payment: Payment,
    payment_intent: StripeObject,
    kind: str,
    amount: str,
    currency: str,
):
    gateway_response = GatewayResponse(
        kind=kind,
        action_required=False,
        transaction_id=payment_intent.id,
        is_success=True,
        amount=price_from_minor_unit(amount, currency),
        currency=payment_intent.currency,
        error=None,
        raw_response=payment_intent.last_response,
        psp_reference=payment_intent.id,
    )

    create_transaction(
        payment,
        kind=kind,
        payment_information=None,  # type: ignore
        action_required=False,
        gateway_response=gateway_response,
    )

    manager = get_plugins_manager()
    discounts = fetch_active_discounts()
    lines = fetch_checkout_lines(checkout)  # type: ignore
    checkout_info = fetch_checkout_info(
        checkout, lines, discounts, manager  # type: ignore
    )
    order, _, _ = complete_checkout(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        payment_data={},
        store_source=False,
        discounts=discounts,
        user=checkout.user or AnonymousUser(),  # type: ignore
        app=None,
    )


def _update_payment_with_new_transaction(
    payment: Payment, stripe_object: StripeObject, kind: str, amount: str, currency: str
):
    gateway_response = GatewayResponse(
        kind=kind,
        action_required=False,
        transaction_id=stripe_object.id,
        is_success=True,
        amount=price_from_minor_unit(amount, currency),
        currency=currency,
        error=None,
        raw_response=stripe_object.last_response,
        psp_reference=stripe_object.id,
    )
    transaction = create_transaction(
        payment,
        kind=kind,
        payment_information=None,  # type: ignore
        action_required=False,
        gateway_response=gateway_response,
    )
    gateway_postprocess(transaction, payment)

    return transaction


def _process_payment_with_checkout(
    payment: Payment,
    payment_intent: StripeObject,
    kind: str,
    amount: str,
    currency: str,
):
    checkout = _get_checkout(payment.id)

    if checkout:
        _finalize_checkout(checkout, payment, payment_intent, kind, amount, currency)


def handle_authorized_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig"
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return
    if payment.order_id:
        if payment.charge_status == ChargeStatus.PENDING:
            _update_payment_with_new_transaction(
                payment,
                payment_intent,
                TransactionKind.AUTH,
                payment_intent.amount,
                payment_intent.currency,
            )
        # Order already created
        return

    if payment.checkout_id:
        _process_payment_with_checkout(
            payment,
            payment_intent,
            kind=TransactionKind.AUTH,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
        )


def handle_failed_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig"
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return
    _update_payment_with_new_transaction(
        payment,
        payment_intent,
        TransactionKind.CANCEL,
        payment_intent.amount,
        payment_intent.currency,
    )
    if payment.order:
        order_voided(payment.order, None, None, payment, get_plugins_manager())


def handle_processing_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig"
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return
    if payment.order_id:
        # Order already created
        return

    if payment.checkout_id:
        _process_payment_with_checkout(
            payment,
            payment_intent,
            TransactionKind.PENDING,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
        )


def handle_successful_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig"
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return
    if payment.order_id:
        if payment.charge_status in [ChargeStatus.PENDING, ChargeStatus.NOT_CHARGED]:
            capture_transaction = _update_payment_with_new_transaction(
                payment,
                payment_intent,
                TransactionKind.CAPTURE,
                payment_intent.amount_received,
                payment_intent.currency,
            )
            order_captured(
                payment.order,  # type: ignore
                None,
                None,
                capture_transaction.amount,
                payment,
                get_plugins_manager(),
            )
        return

    if payment.checkout_id:
        _process_payment_with_checkout(
            payment,
            payment_intent,
            TransactionKind.CAPTURE,
            amount=payment_intent.amount_received,
            currency=payment_intent.currency,
        )


def handle_refund(charge: StripeObject, gateway_config: "GatewayConfig"):
    payment_intent_id = charge.payment_intent
    payment = _get_payment(payment_intent_id)

    refund = charge.refunds.data[0]
    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent_id},
        )
        return

    already_processed = payment.transactions.filter(token=refund.id).exists()

    if already_processed:
        logger.debug(
            "Refund already processed",
            extra={
                "refund": refund.id,
                "payment": payment.id,
                "payment_intent_id": payment_intent_id,
            },
        )
        return

    if payment.charge_status in ChargeStatus.FULLY_REFUNDED:
        logger.info(
            "Order already fully refunded", extra={"order_id": payment.order_id}
        )
        return

    refund_transaction = _update_payment_with_new_transaction(
        payment, refund, TransactionKind.REFUND, refund.amount, refund.currency
    )
    if payment.order:
        order_refunded(
            payment.order,
            None,
            None,
            refund_transaction.amount,
            payment,
            get_plugins_manager(),
        )
