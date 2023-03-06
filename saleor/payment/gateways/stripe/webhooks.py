import logging
from typing import List, Optional

from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Prefetch
from django.http import HttpResponse
from stripe.error import SignatureVerificationError
from stripe.stripe_object import StripeObject

from ....checkout.calculations import calculate_checkout_total_with_gift_cards
from ....checkout.complete_checkout import complete_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....core.transactions import transaction_with_commit_on_errors
from ....discount.utils import fetch_active_discounts
from ....order.actions import order_captured, order_refunded, order_voided
from ....order.fetch import fetch_order_info
from ....order.models import Order
from ....plugins.manager import get_plugins_manager
from ... import ChargeStatus, TransactionKind
from ...gateway import payment_refund_or_void
from ...interface import GatewayConfig, GatewayResponse
from ...models import Payment
from ...utils import (
    create_transaction,
    gateway_postprocess,
    price_from_minor_unit,
    try_void_or_refund_inactive_payment,
    update_payment_charge_status,
    update_payment_method_details,
)
from .consts import (
    WEBHOOK_AUTHORIZED_EVENT,
    WEBHOOK_CANCELED_EVENT,
    WEBHOOK_FAILED_EVENT,
    WEBHOOK_PROCESSING_EVENT,
    WEBHOOK_REFUND_EVENT,
    WEBHOOK_SUCCESS_EVENT,
)
from .stripe_api import (
    construct_stripe_event,
    get_payment_method_details,
    update_payment_method,
)

logger = logging.getLogger(__name__)


@transaction_with_commit_on_errors()
def handle_webhook(
    request: WSGIRequest, gateway_config: "GatewayConfig", channel_slug: str
):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    api_key = gateway_config.connection_params["secret_api_key"]
    endpoint_secret = gateway_config.connection_params.get("webhook_secret")

    if not endpoint_secret:
        logger.warning("Missing webhook secret on Saleor side.")
        response = HttpResponse(status=500)
        response.content = "Missing webhook secret on Saleor side."
        return response

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
            extra={
                "event_type": event.type,
                "event_id": event.id,
                "channel_slug": channel_slug,
            },
        )
        webhook_handlers[event.type](event.data.object, gateway_config, channel_slug)
    else:
        logger.warning(
            "Received unhandled webhook events", extra={"event_type": event.type}
        )
    return HttpResponse(status=200)


def _channel_slug_is_different_from_payment_channel_slug(
    channel_slug: str, payment: Payment
) -> bool:
    checkout = payment.checkout
    order = payment.order
    if checkout is not None:
        return channel_slug != checkout.channel.slug
    elif order is not None:
        return channel_slug != order.channel.slug
    else:
        raise ValueError(
            "Both payment.checkout and payment.order cannot be None"
        )  # pragma: no cover


def _get_payment(payment_intent_id: str) -> Optional[Payment]:
    return (
        Payment.objects.prefetch_related(
            Prefetch("checkout", queryset=Checkout.objects.select_related("channel")),
            Prefetch("order", queryset=Order.objects.select_related("channel")),
        )
        .select_for_update(of=("self",))
        .filter(transactions__token=payment_intent_id)
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

    transaction = create_transaction(
        payment,
        kind=kind,
        payment_information=None,
        action_required=False,
        gateway_response=gateway_response,
    )

    # To avoid zombie payments we have to update payment `charge_status` without
    # changing `to_confirm` flag. In case when order cannot be created then
    # payment will be refunded.
    update_payment_charge_status(payment, transaction)
    payment.refresh_from_db()
    checkout.refresh_from_db()

    manager = get_plugins_manager()
    discounts = fetch_active_discounts()
    lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    if unavailable_variant_pks:
        raise ValidationError("Some of the checkout lines variants are unavailable.")
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    checkout_total = calculate_checkout_total_with_gift_cards(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address or checkout.billing_address,
        discounts=discounts,
    )

    try:
        # when checkout total value is different than total amount from payments
        # it means that some products has been removed during the payment was completed
        if checkout_total.gross.amount != payment.total:
            payment_refund_or_void(payment, manager, checkout_info.channel.slug)
            raise ValidationError(
                "Cannot complete checkout - some products do not exist anymore."
            )

        order, _, _ = complete_checkout(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            payment_data={},
            store_source=False,
            discounts=discounts,
            user=checkout.user or None,
            app=None,
        )
    except ValidationError as e:
        logger.info("Failed to complete checkout %s.", checkout.pk, extra={"error": e})
        return None


def _get_or_create_transaction(
    payment: Payment, stripe_object: StripeObject, kind: str, amount: str, currency: str
):
    transaction = payment.transactions.filter(
        token=stripe_object.id,
        action_required=False,
        is_success=True,
        kind=kind,
    ).last()
    if not transaction:
        transaction = _update_payment_with_new_transaction(
            payment, stripe_object, kind, amount, currency
        )
    return transaction


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
        payment_information=None,
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


def _update_payment_method_metadata(
    payment: Payment,
    payment_intent: StripeObject,
    gateway_config: "GatewayConfig",
) -> None:
    api_key = gateway_config.connection_params["secret_api_key"]
    metadata = payment.metadata

    if metadata:
        update_payment_method(api_key, payment_intent.payment_method, metadata)


def update_payment_method_details_from_intent(
    payment: Payment, payment_intent: StripeObject
):
    if payment_method_info := get_payment_method_details(payment_intent):
        changed_fields: List[str] = []
        update_payment_method_details(payment, payment_method_info, changed_fields)
        if changed_fields:
            payment.save(update_fields=changed_fields)


def handle_authorized_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig", channel_slug: str
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return

    if _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment):
        return

    _update_payment_method_metadata(payment, payment_intent, gateway_config)
    update_payment_method_details_from_intent(payment, payment_intent)

    if not payment.is_active:
        transaction = _get_or_create_transaction(
            payment,
            payment_intent,
            TransactionKind.AUTH,
            payment_intent.amount,
            payment_intent.currency,
        )
        manager = get_plugins_manager()
        try_void_or_refund_inactive_payment(payment, transaction, manager)
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
    payment_intent: StripeObject, _gateway_config: "GatewayConfig", channel_slug: str
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return

    if _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment):
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
    payment_intent: StripeObject, _gateway_config: "GatewayConfig", channel_slug: str
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return

    if _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment):
        return

    if not payment.is_active:
        # we can't cancel/refund processing payment
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
    payment_intent: StripeObject, gateway_config: "GatewayConfig", channel_slug: str
):
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return

    if _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment):
        return

    _update_payment_method_metadata(payment, payment_intent, gateway_config)
    update_payment_method_details_from_intent(payment, payment_intent)

    if not payment.is_active:
        transaction = _get_or_create_transaction(
            payment,
            payment_intent,
            TransactionKind.CAPTURE,
            payment_intent.amount_received,
            payment_intent.currency,
        )
        try_void_or_refund_inactive_payment(payment, transaction, get_plugins_manager())
        return

    if payment.order:
        if payment.charge_status in [ChargeStatus.PENDING, ChargeStatus.NOT_CHARGED]:
            capture_transaction = _update_payment_with_new_transaction(
                payment,
                payment_intent,
                TransactionKind.CAPTURE,
                payment_intent.amount_received,
                payment_intent.currency,
            )
            order_info = fetch_order_info(payment.order)
            order_captured(
                order_info,
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


def handle_refund(
    charge: StripeObject, _gateway_config: "GatewayConfig", channel_slug: str
):
    payment_intent_id = charge.payment_intent
    payment = _get_payment(payment_intent_id)

    refund = charge.refunds.data[0]
    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent_id},
        )
        return

    if _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment):
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
