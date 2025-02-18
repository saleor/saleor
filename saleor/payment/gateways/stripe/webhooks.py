import logging
from typing import cast

import stripe
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.http import HttpResponse
from stripe.error import SignatureVerificationError
from stripe.stripe_object import StripeObject

from ....checkout.calculations import calculate_checkout_total_with_gift_cards
from ....checkout.complete_checkout import complete_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....core.transactions import transaction_with_commit_on_errors
from ....graphql.core import SaleorContext
from ....order.actions import order_charged, order_refunded, order_voided
from ....order.fetch import fetch_order_info
from ....order.models import Order
from ....plugins.manager import get_plugins_manager
from ... import ChargeStatus, TransactionKind
from ...gateway import payment_refund_or_void
from ...interface import GatewayConfig, GatewayResponse
from ...models import Payment, Transaction
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
    request: SaleorContext, gateway_config: "GatewayConfig", channel_slug: str
):
    payload = request.body
    sig_header = request.headers["stripe-signature"]
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
            "Received invalid payload for Stripe webhook", extra={"error": str(e)}
        )
        return HttpResponse(status=400)
    except SignatureVerificationError as e:
        # Invalid signature
        logger.warning("Invalid signature for Stripe webhook", extra={"error": str(e)})
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
    if order is not None:
        return channel_slug != order.channel.slug
    logger.warning(
        "Both payment.checkout and payment.order cannot be None",
        extra={"payment_id": payment.id},
    )
    return True


def _get_payment(payment_intent_id: str, with_lock=True) -> Payment | None:
    qs = Payment.objects.prefetch_related(
        Prefetch("checkout", queryset=Checkout.objects.select_related("channel")),
        Prefetch("order", queryset=Order.objects.select_related("channel")),
    )
    if with_lock:
        qs = qs.select_for_update(of=("self",))
    return qs.filter(transactions__token=payment_intent_id).first()


def _get_checkout(payment_id: int) -> Checkout | None:
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

    transaction = Transaction.objects.filter(
        payment_id=payment.id,
        is_success=True,
        action_required=False,
        kind=kind,
    ).first()

    # Ensure that the transaction does not exist before creating it. The transaction
    # can be created by the `checkoutComplete` logic, which can be executed
    # simultaneously with this function.
    if not transaction:
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

    manager = get_plugins_manager(allow_replica=False)
    lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    if unavailable_variant_pks:
        payment_refund_or_void(payment, manager, checkout.channel.slug)
        raise ValidationError("Some of the checkout lines variants are unavailable.")
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_total = calculate_checkout_total_with_gift_cards(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address or checkout.billing_address,
    )

    try:
        # when checkout total amount is less than total amount from payments
        # it means that something changed in the checkout and we make a refund
        # if the checkout is overpaid we allow to create the order and handle it
        # by staff.
        if checkout_total.gross.amount > payment.total:
            payment_refund_or_void(payment, manager, checkout_info.channel.slug)
            raise ValidationError(
                "Cannot complete checkout - payment doesn't cover the checkout total."
            )

        order, _, _ = complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data={},
            store_source=False,
            user=checkout.user or None,
            app=None,
        )
    except ValidationError as e:
        logger.info(
            "Failed to complete checkout %s.", checkout.pk, extra={"error": str(e)}
        )


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
    checkout: Checkout,
    kind: str,
    amount: str,
    currency: str,
):
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
        changed_fields: list[str] = []
        update_payment_method_details(payment, payment_method_info, changed_fields)
        if changed_fields:
            payment.save(update_fields=changed_fields)


def handle_authorized_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig", channel_slug: str
):
    payment = _get_payment(payment_intent.id, with_lock=False)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return

    # We apply the lock in the same order as in the checkoutComplete logic. By
    # reverting these calls we have a risk of deadlocks.
    checkout = _get_checkout(payment.id)
    payment = _get_payment(payment_intent.id, with_lock=True)
    # payment was already fetch, we are sure that it exists
    payment = cast(Payment, payment)

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
        manager = get_plugins_manager(allow_replica=False)
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

    if checkout:
        _process_payment_with_checkout(
            payment,
            payment_intent,
            checkout=checkout,
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
        order_voided(
            payment.order, None, None, payment, get_plugins_manager(allow_replica=False)
        )


def handle_processing_payment_intent(
    payment_intent: StripeObject, _gateway_config: "GatewayConfig", channel_slug: str
):
    payment = _get_payment(payment_intent.id, with_lock=False)

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

    # We apply the lock in the same order as in the checkoutComplete logic. By
    # reverting these calls we have a risk of deadlocks.
    checkout = _get_checkout(payment.id)
    payment = _get_payment(payment_intent.id, with_lock=True)
    # payment was already fetch, we are sure that it exists
    payment = cast(Payment, payment)

    if checkout:
        _process_payment_with_checkout(
            payment,
            payment_intent,
            checkout,
            TransactionKind.PENDING,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
        )


def handle_successful_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig", channel_slug: str
):
    payment = _get_payment(payment_intent.id, with_lock=False)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent was not found",
            extra={"payment_intent": payment_intent.id},
        )
        return

    # We apply the lock in the same order as in the checkoutComplete logic. By
    # reverting these calls we have a risk of deadlocks.
    checkout = _get_checkout(payment.id)
    payment = _get_payment(payment_intent.id, with_lock=True)
    # payment was already fetch, we are sure that it exists
    payment = cast(Payment, payment)

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
        try_void_or_refund_inactive_payment(
            payment, transaction, get_plugins_manager(allow_replica=False)
        )
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
            order_charged(
                order_info,
                None,
                None,
                capture_transaction.amount,
                payment,
                get_plugins_manager(allow_replica=False),
            )
        return

    if checkout:
        _process_payment_with_checkout(
            payment,
            payment_intent,
            checkout=checkout,
            kind=TransactionKind.CAPTURE,
            amount=payment_intent.amount_received,
            currency=payment_intent.currency,
        )


def handle_refund(
    charge: StripeObject, gateway_config: "GatewayConfig", channel_slug: str
):
    payment_intent_id = charge.payment_intent
    payment = _get_payment(payment_intent_id)

    # stripe introduced breaking change and in newer version of api
    # charge object doesn't contain refunds by default
    if not getattr(charge, "refunds", None):
        api_key = gateway_config.connection_params["secret_api_key"]
        charge_with_refunds = stripe.Charge.retrieve(
            charge.stripe_id,
            api_key=api_key,
            expand=["refunds"],
        )
        charge.refunds = charge_with_refunds.refunds
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
            get_plugins_manager(allow_replica=False),
        )
