import base64
import binascii
import hashlib
import hmac
import json
import logging
from decimal import Decimal
from json.decoder import JSONDecodeError
from typing import Any, Callable, Dict, Iterable, List, Optional, cast
from urllib.parse import urlencode, urlparse

import Adyen
import graphene
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.forms.models import model_to_dict
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    QueryDict,
)
from django.http.request import HttpHeaders
from django.http.response import HttpResponseRedirect
from graphql import GraphQLError

from ....checkout.calculations import calculate_checkout_total_with_gift_cards
from ....checkout.complete_checkout import complete_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....core.prices import quantize_price
from ....core.transactions import transaction_with_commit_on_errors
from ....core.utils.url import prepare_url
from ....graphql.core.utils import from_global_id_or_error
from ....order.actions import (
    cancel_order,
    order_authorized,
    order_charged,
    order_refunded,
)
from ....order.events import external_notification_event
from ....order.fetch import fetch_order_info
from ....payment.models import Payment, Transaction
from ....plugins.manager import get_plugins_manager
from ... import ChargeStatus, PaymentError, TransactionKind, gateway
from ...gateway import payment_refund_or_void
from ...interface import GatewayConfig, GatewayResponse
from ...utils import (
    create_payment_information,
    create_transaction,
    gateway_postprocess,
    price_from_minor_unit,
    try_void_or_refund_inactive_payment,
)
from .utils.common import (
    FAILED_STATUSES,
    api_call,
    call_refund,
    initialize_adyen_client,
)

logger = logging.getLogger(__name__)


def get_payment_id(
    payment_id: Optional[str],
    transaction_id: Optional[str] = None,
):
    if payment_id is None or not payment_id.strip():
        logger.warning("Missing payment ID. Reference %s", transaction_id)
        return None
    try:
        _type, db_payment_id = from_global_id_or_error(
            payment_id, only_type="Payment", raise_error=True
        )
    except (UnicodeDecodeError, binascii.Error, GraphQLError):
        logger.warning(
            "Unable to decode the payment ID %s. Reference %s",
            payment_id,
            transaction_id,
        )
        return None
    return db_payment_id


def get_payment(
    payment_id: Optional[str],
    transaction_id: Optional[str] = None,
    check_if_active=True,
) -> Optional[Payment]:
    transaction_id = transaction_id or ""
    db_payment_id = get_payment_id(payment_id)
    if not db_payment_id:
        return None
    payments = (
        Payment.objects.prefetch_related("order", "checkout")
        .select_for_update(of=("self",))
        .filter(id=db_payment_id, gateway="mirumee.payments.adyen")
    )
    if check_if_active:
        payments = payments.filter(is_active=True)
    payment = payments.first()
    if not payment:
        logger.warning(
            "Payment for %s (%s) was not found. Reference %s",
            payment_id,
            db_payment_id,
            transaction_id,
        )
    return payment


def get_checkout(payment_id: int) -> Optional[Checkout]:
    # Lock checkout in the same way as in checkoutComplete
    return (
        Checkout.objects.select_for_update(of=("self",))
        .prefetch_related(
            "gift_cards",
            "lines__variant__product",
        )
        .select_related("shipping_method__shipping_zone")
        .filter(payments__id=payment_id)
        .first()
    )


def get_transaction(
    payment: "Payment",
    transaction_id: Optional[str],
    kind: str,
) -> Optional[Transaction]:
    transaction = payment.transactions.filter(kind=kind, token=transaction_id).last()
    return transaction


def create_new_transaction(notification, payment, kind):
    transaction_id = notification.get("pspReference")
    currency = notification.get("amount", {}).get("currency")
    amount = price_from_minor_unit(
        notification.get("amount", {}).get("value"), currency
    )
    is_success = True if notification.get("success") == "true" else False

    gateway_response = GatewayResponse(
        kind=kind,
        action_required=False,
        transaction_id=transaction_id,
        is_success=is_success,
        amount=amount,
        currency=currency,
        error="",
        raw_response=notification,
        psp_reference=transaction_id,
    )
    return create_transaction(
        payment,
        kind=kind,
        payment_information=None,
        action_required=False,
        gateway_response=gateway_response,
    )


def create_payment_notification_for_order(
    payment: Payment, success_msg: str, failed_msg: Optional[str], is_success: bool
):
    if not payment.order:
        # Order is not assigned
        return
    msg = success_msg if is_success else failed_msg

    external_notification_event(
        order=payment.order,
        user=None,
        app=None,
        message=msg,
        parameters={"service": payment.gateway, "id": payment.token},
    )


def create_order(payment, checkout, manager):
    try:
        lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        if unavailable_variant_pks:
            payment_refund_or_void(payment, manager, checkout.channel.slug)
            raise ValidationError(
                "Some of the checkout lines variants are unavailable."
            )
        checkout_info = fetch_checkout_info(checkout, lines, manager)
        checkout_total = calculate_checkout_total_with_gift_cards(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=checkout.shipping_address or checkout.billing_address,
        )
        # when checkout total value is different than total amount from payments
        # it means that some products has been removed during the payment was completed
        if checkout_total.gross.amount != payment.total:
            payment_refund_or_void(payment, manager, checkout_info.channel.slug)
            raise ValidationError(
                "Cannot create order - some products do not exist anymore."
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
            "Failed to create order from checkout %s.", checkout.pk, extra={"error": e}
        )
        return None
    # Refresh the payment to assign the newly created order
    payment.refresh_from_db()
    return order


def handle_not_created_order(notification, payment, checkout, kind, manager):
    """Process the notification in case when payment doesn't have assigned order."""

    # We don't want to create order for payment that is cancelled or refunded
    if payment.charge_status not in {
        ChargeStatus.NOT_CHARGED,
        ChargeStatus.PENDING,
        ChargeStatus.PARTIALLY_CHARGED,
        ChargeStatus.FULLY_CHARGED,
    }:
        return

    transaction = create_new_transaction(
        notification, payment, TransactionKind.ACTION_TO_CONFIRM
    )

    # Only when we confirm that notification is success we will create the order
    if transaction.is_success and checkout:
        confirm_payment_and_set_back_to_confirm(payment, manager, checkout.channel.slug)
        payment.refresh_from_db()  # refresh charge_status
        order = create_order(payment, checkout, manager)
        return order
    return None


def handle_authorization(notification: Dict[str, Any], gateway_config: GatewayConfig):
    """Handle authorization notification.

    Handler for processing an authorization notification from Adyen. The notification
    is async so we assume that it can be delivered in two different situations: order
    is already created, order is not created yet.
        - order is already created: we process notification and update the status of
        payment and order in case if we didn't do that previously.
        - order is not created yet: we create an order and update a payment's status.
        In case when checkout_complete raises an exception we will call a refund/void
        for a given payment.
    For both cases we will include an external event to Order history.
    No matter if Adyen has enabled auto capture on their side, we will always receive
    authorization notification. In that case, we can't determine if the payment on
    their side goes to authorization or captured status.
    """

    transaction_id = notification.get("pspReference")
    graphql_payment_id = notification.get("merchantReference")
    payment_id = get_payment_id(graphql_payment_id, transaction_id)
    if not payment_id:
        # We can't decode the merchantReference which should be a payment id in
        # graphql format
        return

    checkout = get_checkout(payment_id)

    payment = get_payment(
        notification.get("merchantReference"), transaction_id, check_if_active=False
    )
    if not payment:
        # We don't know anything about that payment
        return

    manager = get_plugins_manager()
    adyen_auto_capture = gateway_config.connection_params["adyen_auto_capture"]
    kind = TransactionKind.AUTH
    if adyen_auto_capture:
        kind = TransactionKind.CAPTURE

    amount = notification.get("amount", {})
    try:
        notification_payment_amount = price_from_minor_unit(
            amount.get("value"), amount.get("currency")
        )
    except TypeError as e:
        logger.exception("Cannot convert amount from minor unit", extra={"error": e})
        return

    if notification_payment_amount < payment.total:
        # If amount from the notification is lower than payment total then we have
        # a partial payment so we create an order in separate webhook (order_closed)
        # after payment finished.
        logger.info(
            f"This is a partial payment notification. We can't create an order. "
            f"pspReference: {transaction_id}, payment_id: {payment.pk}"
        )
        return

    transaction = get_transaction(payment, transaction_id, kind)

    if not payment.is_active:
        if not transaction:
            transaction = create_new_transaction(notification, payment, kind)
        transaction = cast(Transaction, transaction)
        try_void_or_refund_inactive_payment(payment, transaction, manager)
        return

    if not transaction:
        if not payment.order:
            handle_not_created_order(notification, payment, checkout, kind, manager)
        else:
            new_transaction = create_new_transaction(notification, payment, kind)
            if new_transaction.is_success:
                gateway_postprocess(new_transaction, payment)
                if adyen_auto_capture:
                    order_info = fetch_order_info(payment.order)
                    order_charged(
                        order_info,
                        None,
                        None,
                        new_transaction.amount,
                        payment,
                        manager,
                    )
                else:
                    order_authorized(
                        payment.order,
                        None,
                        None,
                        new_transaction.amount,
                        payment,
                        manager,
                    )

    reason = notification.get("reason", "-")
    is_success = True if notification.get("success") == "true" else False
    success_msg = f"Adyen: The payment  {transaction_id} request  was successful."
    failed_msg = (
        f"Adyen: The payment {transaction_id} request failed. Reason: {reason}."
    )
    create_payment_notification_for_order(payment, success_msg, failed_msg, is_success)


def handle_cancellation(
    notification: Dict[str, Any],
    _gateway_config: GatewayConfig,
):
    # https://docs.adyen.com/checkout/cancel#cancellation-notifciation
    transaction_id = notification.get("pspReference")
    payment = get_payment(
        # check_if_active=False as the payment can be still active or already cancelled
        notification.get("merchantReference"),
        transaction_id,
        check_if_active=False,
    )
    if not payment:
        return
    transaction = get_transaction(payment, transaction_id, TransactionKind.CANCEL)
    if transaction and transaction.is_success:
        # it is already cancelled
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.CANCEL
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    success_msg = f"Adyen: The cancel {transaction_id} request was successful."
    failed_msg = f"Adyen: The cancel {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, new_transaction.is_success
    )
    if payment.order and new_transaction.is_success:
        manager = get_plugins_manager()
        cancel_order(payment.order, None, None, manager)


def handle_cancel_or_refund(
    notification: Dict[str, Any], gateway_config: GatewayConfig
):
    # https://docs.adyen.com/checkout/cancel-or-refund#cancel-or-refund-notification
    additional_data = notification.get("additionalData")
    if not additional_data:
        return
    action = additional_data.get("modification.action")
    if action == "refund":
        handle_refund(notification, gateway_config)
    elif action == "cancel":
        handle_cancellation(notification, gateway_config)


def handle_capture(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    # https://docs.adyen.com/checkout/capture#capture-notification
    transaction_id = notification.get("pspReference")
    graphql_payment_id = notification.get("merchantReference")

    payment_id = get_payment_id(graphql_payment_id, transaction_id)
    if not payment_id:
        return
    checkout = get_checkout(payment_id)

    payment = get_payment(graphql_payment_id, transaction_id, check_if_active=False)
    if not payment:
        return

    manager = get_plugins_manager()

    transaction = get_transaction(payment, transaction_id, TransactionKind.CAPTURE)

    if not payment.is_active:
        if not transaction:
            transaction = create_new_transaction(
                notification, payment, TransactionKind.CAPTURE
            )
        transaction = cast(Transaction, transaction)
        try_void_or_refund_inactive_payment(payment, transaction, manager)
        return

    if not transaction:
        if not payment.order:
            handle_not_created_order(
                notification, payment, checkout, TransactionKind.CAPTURE, manager
            )
        else:
            new_transaction = create_new_transaction(
                notification, payment, TransactionKind.CAPTURE
            )
            if new_transaction.is_success:
                gateway_postprocess(new_transaction, payment)
                order_info = fetch_order_info(payment.order)
                order_charged(
                    order_info, None, None, new_transaction.amount, payment, manager
                )

    reason = notification.get("reason", "-")
    is_success = True if notification.get("success") == "true" else False
    success_msg = f"Adyen: The capture {transaction_id} request was successful."
    failed_msg = f"Adyen: The capture {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(payment, success_msg, failed_msg, is_success)


def handle_failed_capture(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    # https://docs.adyen.com/checkout/capture#failed-capture
    transaction_id = notification.get("pspReference")
    payment = get_payment(
        notification.get("merchantReference"), transaction_id, check_if_active=False
    )
    if not payment:
        return

    transaction = get_transaction(
        payment, transaction_id, TransactionKind.CAPTURE_FAILED
    )
    if transaction and transaction.is_success:
        # it is already failed
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.CAPTURE_FAILED
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    msg = (
        f"Adyen: The capture for {transaction_id} failed due to a technical issue. "
        f"Reason: {reason}"
    )
    create_payment_notification_for_order(payment, msg, None, True)


def handle_pending(notification: Dict[str, Any], gateway_config: GatewayConfig):
    # https://docs.adyen.com/development-resources/webhooks/understand-notifications#
    # event-codes"
    transaction_id = notification.get("pspReference")
    payment = get_payment(
        notification.get("merchantReference"), transaction_id, check_if_active=False
    )
    if not payment:
        return
    transaction = get_transaction(payment, transaction_id, TransactionKind.PENDING)
    if transaction and transaction.is_success:
        # it is already pending
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.PENDING
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    msg = f"Adyen: The transaction {transaction_id} is pending. Reason: {reason}"
    create_payment_notification_for_order(
        payment, msg, None, new_transaction.is_success
    )


def handle_refund(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    # https://docs.adyen.com/checkout/refund#refund-notification
    transaction_id = notification.get("pspReference")
    payment = get_payment(
        notification.get("merchantReference"), transaction_id, check_if_active=False
    )
    if not payment:
        return

    transaction = get_transaction(payment, transaction_id, TransactionKind.REFUND)
    if not transaction or not transaction.already_processed:
        if not transaction:
            transaction = create_new_transaction(
                notification, payment, TransactionKind.REFUND
            )
        gateway_postprocess(transaction, payment)
    else:
        # it is already refunded
        return
    transaction = cast(Transaction, transaction)
    reason = notification.get("reason", "-")
    success_msg = f"Adyen: The refund {transaction_id} request was successful."
    failed_msg = f"Adyen: The refund {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, transaction.is_success
    )
    if payment.order and transaction.is_success:
        order_refunded(
            payment.order,
            None,
            None,
            transaction.amount,
            payment,
            get_plugins_manager(),
        )


def _get_kind(transaction: Optional[Transaction]) -> str:
    if transaction:
        return transaction.kind
    # To proceed the refund we already need to have the capture status so we will use it
    return TransactionKind.CAPTURE


def handle_failed_refund(notification: Dict[str, Any], gateway_config: GatewayConfig):
    # https://docs.adyen.com/checkout/refund#failed-refund
    transaction_id = notification.get("pspReference")
    payment = get_payment(
        notification.get("merchantReference"), transaction_id, check_if_active=False
    )
    if not payment:
        return

    # take the last status of payment before we tried to perform the refund
    last_transaction = payment.transactions.filter(
        action_required=False,
        is_success=True,
        kind__in=[TransactionKind.AUTH, TransactionKind.CAPTURE],
    ).last()
    last_kind = _get_kind(last_transaction)

    refund_transaction = payment.transactions.filter(
        token=transaction_id,
        kind__in=[
            TransactionKind.REFUND_ONGOING,
            TransactionKind.REFUND,
            TransactionKind.REFUND_FAILED,
        ],
    ).last()

    reason = notification.get("reason", "-")
    msg = (
        f"Adyen: The refund {transaction_id} failed due to a technical issue. If you"
        f" receive more than two failures on the same refund, contact Adyen Support "
        f"Team. Reason: {reason}"
    )
    create_payment_notification_for_order(payment, msg, None, True)

    if not refund_transaction:
        # we don't know anything about refund so we have to skip the notification about
        # failed refund.
        return

    if refund_transaction.kind == TransactionKind.REFUND_FAILED:
        # The failed refund is already saved
        return
    elif refund_transaction.kind == TransactionKind.REFUND_ONGOING:
        # create new failed transaction which will allows us to discover duplicated
        # notification
        create_new_transaction(notification, payment, TransactionKind.REFUND_FAILED)

        # Refund ongoing doesnt do any action on payment.capture_amount so we set
        # 0 to amount. Thanks to it we can create transaction with the same status and
        # no worries that we will capture total in payment two times.
        # (if gateway_postprocess gets transaction with capture it will subtract the
        # amount from transaction
        notification["amount"]["value"] = 0
        new_transaction = create_new_transaction(notification, payment, last_kind)
        gateway_postprocess(new_transaction, payment)
    elif refund_transaction.kind == TransactionKind.REFUND:
        # create new failed transaction which will allows us to discover duplicated
        # notification
        create_new_transaction(notification, payment, TransactionKind.REFUND_FAILED)
        new_transaction = create_new_transaction(
            notification, payment, TransactionKind.CAPTURE
        )
        gateway_postprocess(new_transaction, payment)


def handle_reversed_refund(
    notification: Dict[str, Any], _gateway_config: GatewayConfig
):
    # https://docs.adyen.com/checkout/refund#failed-refund
    transaction_id = notification.get("pspReference")
    payment = get_payment(
        notification.get("merchantReference"), transaction_id, check_if_active=False
    )
    if not payment:
        return
    transaction = get_transaction(
        payment, transaction_id, TransactionKind.REFUND_REVERSED
    )

    if transaction:
        # it is already refunded
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.REFUND_REVERSED
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    msg = (
        f"Adyen: The refunded amount from {transaction_id} has been returned to Adyen, "
        f"and is back in your account. This may happen if the shopper's bank account "
        f"is no longer valid. Reason: {reason}"
    )
    create_payment_notification_for_order(payment, msg, msg, True)


def handle_refund_with_data(
    notification: Dict[str, Any], gateway_config: GatewayConfig
):
    # https://docs.adyen.com/checkout/refund#refund-with-data
    handle_refund(notification, gateway_config)


def webhook_not_implemented(
    notification: Dict[str, Any], gateway_config: GatewayConfig
):
    adyen_id = notification.get("pspReference")
    success = notification.get("success", True)
    event = notification.get("eventCode")
    transaction_id = notification.get("pspReference")
    payment = get_payment(notification.get("merchantReference"), transaction_id)
    if not payment:
        return
    msg = (
        f"Received not implemented notification from Adyen. Event name: {event}, "
        f"success: {success}, adyen reference: {adyen_id}."
    )
    create_payment_notification_for_order(payment, msg, None, True)


def handle_order_opened(notification: Dict[str, Any], gateway_config: GatewayConfig):
    # From Adyen's documentation:
    # Sent when the first payment for your payment request is a partial payment, and an
    # order has been created.
    #
    # In this case we just logging here that we received the webhook properly.
    logger.info(f"First payment request as a partial payment. {notification}")


def get_or_create_adyen_partial_payments(
    notification: Dict[str, Any], payment: Payment
) -> Optional[List[Payment]]:
    """Store basic data about partial payments created by Adyen.

    This is a workaround for not supporting partial payments in Saleor. Adyen can
    handle partial payments on their side and send us info about them. We want to
    somehow store some basic information about this but without modifying a whole
    Saleor logic. We're going to change it by introducing partial payments feature on
    Saleor side.
    """
    additional_data = notification.get("additionalData", {})
    new_payments = []
    currency = payment.currency
    payment_total_to_cover = payment.total
    for (
        payment_method_key,
        payment_amount_key,
        psp_reference_key,
    ) in get_adyen_partial_payment_keys(additional_data):
        # payment amount key has structure - "{currency} {amount}", like 'GBP 41.90',
        # for payments with 3d secure, the last payment could not have an amount field,
        # in that case we need to handle it on our side.
        if payment_amount_key in additional_data:
            currency, amount = additional_data[payment_amount_key].split()
            amount = Decimal(amount)
        else:
            amount = quantize_price(max(payment_total_to_cover, Decimal(0)), currency)

        new_payment = Payment(**model_to_dict(payment, exclude=["id", "checkout"]))
        new_payment.checkout_id = payment.checkout_id
        new_payment.is_active = False
        new_payment.partial = True
        new_payment.total = Decimal(amount)
        # Increasing captured amount increases a total paid of the order.
        new_payment.captured_amount = 0
        new_payment.currency = currency
        new_payment.payment_method_type = additional_data.get(
            payment_method_key, "givex"
        )
        new_payment.psp_reference = additional_data.get(psp_reference_key, "")
        new_payment.extra_data = json.dumps({"parent_payment_id": payment.id})
        new_payments.append(new_payment)

        # For some last partial payments Adyen doesn't send an amount field. We need to
        # figure it out somehow, we calculate the total of amount covered by previous
        # payments.
        payment_total_to_cover -= new_payment.total

    already_existing_partial_payments = (
        Payment.objects.filter(
            psp_reference__in=[p.psp_reference for p in new_payments],
            partial=True,
            checkout_id=payment.checkout_id,
        )
        if payment.checkout_id
        else []
    )
    if already_existing_partial_payments:
        return list(already_existing_partial_payments)

    if new_payments:
        return Payment.objects.bulk_create(new_payments)
    return None


def create_order_event_about_adyen_partial_payments(
    adyen_partial_payments: Iterable[Payment], payment
):
    msg = "Adyen: "

    for payment in adyen_partial_payments:
        payment_method = payment.payment_method_type
        payment_amount = payment.total
        psp_reference = payment.psp_reference
        currency = payment.currency
        msg += (
            f"Partial payment with {payment_method} (PSP: {psp_reference}) "
            f"for {currency} {payment_amount}.\n"
        )
    if adyen_partial_payments:
        payment.refresh_from_db()
        create_payment_notification_for_order(
            payment, msg, failed_msg=None, is_success=True
        )


def get_adyen_partial_payment_keys(additiona_data):
    """Get keys that contains adyen partial data.

    The data received from Adyen has strange structure. In middle of dict key, there is
    a int number pointing to the given payment method. So we need to convert it and
    match somehow a paymentMethod, paymentAmount and payment psp reference
    """
    index = 1
    while True:
        payment_method_key = f"order-{index}-paymentMethod"
        payment_amount_key = f"order-{index}-paymentAmount"
        psp_reference_key = f"order-{index}-pspReference"

        # stop iterating when there is no more an additional payment method fields
        if payment_method_key not in additiona_data:
            return
        yield (payment_method_key, payment_amount_key, psp_reference_key)
        index += 1


def refund_partial_payments(payments, config):
    for payment in payments:
        adyen_client = initialize_adyen_client(config)
        merchant_account = config.connection_params["merchant_account"]
        logger.info("Calling refund for partial payment: %s", payment.psp_reference)
        call_refund(
            amount=payment.total,
            currency=payment.currency,
            merchant_account=merchant_account,
            token=payment.psp_reference,
            graphql_payment_id=graphene.Node.to_global_id("Payment", payment.pk),
            adyen_client=adyen_client,
        )


def handle_order_closed(notification: Dict[str, Any], gateway_config: GatewayConfig):
    # From Adyen's documentation:
    # The success field informs you of the outcome of the shopper's last payment when
    # paying for an order in partial payments.
    #
    # Possible values:
    # true: The full amount has been paid.
    # false: The shopper did not pay the full amount within the sessionValidity.
    # All partial payments that were processed previously are automatically cancelled
    # or refunded.
    is_success = True if notification.get("success") == "true" else False
    psp_reference = notification.get("pspReference")
    logger.info(
        f"Partial payment has been finished with result: {is_success}."
        f"psp: {psp_reference}"
    )

    if not is_success:
        logger.info(
            "The shopper did not pay the full amount within the "
            "sessionValidity. All partial payments that were processed "
            "previously are automatically cancelled or refunded by Adyen."
        )
        return
    payment = get_payment(
        notification.get("merchantReference"), psp_reference, check_if_active=False
    )

    if not payment:
        # We don't know anything about that payment
        logger.info(f"There is no payment with psp: {psp_reference}")
        return

    if payment.order:
        logger.info(f"Order already created for payment: {payment.pk}")
        return

    adyen_partial_payments = get_or_create_adyen_partial_payments(notification, payment)
    if not payment.is_active:
        logger.info(
            "Immediately refund an Adyen payments: %s as payment %s is not active."
        )
        refund_partial_payments(adyen_partial_payments, config=gateway_config)
        return

    checkout = payment.checkout

    adyen_auto_capture = gateway_config.connection_params["adyen_auto_capture"]
    kind = TransactionKind.CAPTURE if adyen_auto_capture else TransactionKind.AUTH

    order = None
    try:
        order = handle_not_created_order(
            notification, payment, checkout, kind, get_plugins_manager()
        )
    except Exception as e:
        logger.exception("Exception during order creation", extra={"error": e})
        return
    finally:
        if not order and adyen_partial_payments:
            refund_partial_payments(adyen_partial_payments, config=gateway_config)
            # There is a possibility that user will try once again to pay with partial
            # payments, we update partial objects, as we agree that partial==True points
            # always to valid payments. This is temporary workaround to handle Adyen
            # partial payments in 3.0, and will be properly handled in partial payment
            # feature.
            Payment.objects.filter(
                id__in=[p.id for p in adyen_partial_payments]
            ).update(partial=False)

    if adyen_partial_payments:
        create_order_event_about_adyen_partial_payments(adyen_partial_payments, payment)
    else:
        reason = notification.get("reason", "-")
        success_msg = f"Adyen: The payment  {psp_reference} request  was successful."
        failed_msg = (
            f"Adyen: The payment {psp_reference} request failed. Reason: {reason}."
        )
        create_payment_notification_for_order(
            payment, success_msg, failed_msg, is_success
        )


EVENT_MAP = {
    "AUTHORISATION": handle_authorization,
    "AUTHORISATION_ADJUSTMENT": webhook_not_implemented,
    "CANCELLATION": handle_cancellation,
    "CANCEL_OR_REFUND": handle_cancel_or_refund,
    "CAPTURE": handle_capture,
    "CAPTURE_FAILED": handle_failed_capture,
    "HANDLED_EXTERNALLY": webhook_not_implemented,
    "ORDER_OPENED": handle_order_opened,
    "ORDER_CLOSED": handle_order_closed,
    "PENDING": handle_pending,
    "PROCESS_RETRY": webhook_not_implemented,
    "REFUND": handle_refund,
    "REFUND_FAILED": handle_failed_refund,
    "REFUNDED_REVERSED": handle_reversed_refund,
    "REFUND_WITH_DATA": handle_refund_with_data,
    "REPORT_AVAILABLE": webhook_not_implemented,
    "VOID_PENDING_REFUND": webhook_not_implemented,
}


def validate_hmac_signature(
    notification: Dict[str, Any], gateway_config: "GatewayConfig"
) -> bool:
    hmac_signature: Optional[str] = notification.get("additionalData", {}).get(
        "hmacSignature"
    )
    hmac_key: Optional[str] = gateway_config.connection_params.get("webhook_hmac")
    if not hmac_key:
        return not hmac_signature

    if not hmac_signature:
        return False

    hmac_key = hmac_key.encode()

    success = "true" if notification.get("success", "") == "true" else "false"
    if notification.get("success", None) is None:
        success = ""

    payload_list = [
        notification.get("pspReference", ""),
        notification.get("originalReference", ""),
        notification.get("merchantAccountCode", ""),
        notification.get("merchantReference", ""),
        str(notification.get("amount", {}).get("value", "")),
        notification.get("amount", {}).get("currency", ""),
        notification.get("eventCode", ""),
        success,
    ]
    payload = ":".join(payload_list)

    hmac_key = binascii.a2b_hex(hmac_key)
    hm = hmac.new(hmac_key, payload.encode("utf-8"), hashlib.sha256)
    expected_merchant_sign = base64.b64encode(hm.digest())
    return hmac.compare_digest(hmac_signature, expected_merchant_sign.decode("utf-8"))


def validate_auth_user(headers: HttpHeaders, gateway_config: "GatewayConfig") -> bool:
    username = gateway_config.connection_params["webhook_user"]
    password = gateway_config.connection_params["webhook_user_password"]
    auth_header: Optional[str] = headers.get("Authorization")
    if not auth_header and not username:
        return True
    if auth_header and not username:
        return False
    if not auth_header and username:
        return False

    split_auth = auth_header.split(maxsplit=1)  # type: ignore
    prefix = "BASIC"

    if len(split_auth) != 2 or split_auth[0].upper() != prefix:
        return False

    auth = split_auth[1]
    try:
        decoded_auth = base64.b64decode(auth).decode()
        request_username, request_password = decoded_auth.split(":")
        user_is_correct = request_username == username
        if user_is_correct and check_password(request_password, password):
            return True
    except binascii.Error:
        pass
    return False


def validate_merchant_account(
    notification: Dict[str, Any], gateway_config: "GatewayConfig"
):
    merchant_account_code = notification.get("merchantAccountCode")
    return merchant_account_code == gateway_config.connection_params.get(
        "merchant_account"
    )


@transaction_with_commit_on_errors()
def handle_webhook(request: WSGIRequest, gateway_config: "GatewayConfig"):
    try:
        json_data = json.loads(request.body)
    except JSONDecodeError:
        logger.warning("Cannot parse request body.")
        return HttpResponse("[accepted]")
    # JSON and HTTP POST notifications always contain a single NotificationRequestItem
    # object.
    notification = json_data.get("notificationItems")[0].get(
        "NotificationRequestItem", {}
    )

    if not validate_merchant_account(notification, gateway_config):
        logger.warning("Not supported merchant account.")
        return HttpResponse("[accepted]")
    if not validate_hmac_signature(notification, gateway_config):
        return HttpResponseBadRequest("Invalid or missing hmac signature.")
    if not validate_auth_user(request.headers, gateway_config):
        return HttpResponseBadRequest("Invalid or missing basic auth.")

    event_handler = EVENT_MAP.get(notification.get("eventCode", ""))
    if event_handler:
        event_handler(notification, gateway_config)
        return HttpResponse("[accepted]")
    return HttpResponse("[accepted]")


class HttpResponseRedirectWithTrustedProtocol(HttpResponseRedirect):
    def __init__(self, redirect_to: str, *args, **kwargs) -> None:
        parsed = urlparse(redirect_to)
        self.allowed_schemes = [parsed.scheme]
        super().__init__(redirect_to, *args, **kwargs)


@transaction_with_commit_on_errors()
def handle_additional_actions(
    request: WSGIRequest, payment_details: Callable, channel_slug: str
):
    """Handle redirect with additional actions.

    When a customer uses a payment method with redirect, before customer is redirected
    back to storefront, the request goes through the Saleor. We use the data received
    from Adyen, as a query params or as a post data, to finalize an additional action.
    After that, if payment doesn't require any additional action we create an order.
    In case if action data exists, we don't create an order and we include them in url.
    """
    payment_id = request.GET.get("payment")
    checkout_pk = request.GET.get("checkout")

    if not payment_id or not checkout_pk:
        logger.warning(
            "Missing payment_id or checkout id in Adyen's request.",
            extra={"payment_id": payment_id, "checkout_id": checkout_pk},
        )
        return HttpResponseNotFound()
    db_payment_id = get_payment_id(payment_id)
    checkout = get_checkout(db_payment_id)
    payment = get_payment(payment_id, transaction_id=None)
    if not payment:
        logger.warning(
            "Payment doesn't exist or is not active.", extra={"payment_id": payment_id}
        )
        return HttpResponseNotFound(
            "Cannot perform payment. There is no active Adyen payment."
        )

    # Adyen for some payment methods can call success notification before we will
    # call an additional_action.
    if not payment.order_id:
        if not checkout or str(checkout.token) != checkout_pk:
            logger.warning(
                "There is no checkout with this payment.",
                extra={"checkout_pk": checkout_pk, "payment_id": payment_id},
            )
            return HttpResponseNotFound(
                "Cannot perform payment. There is no checkout with this payment."
            )

    extra_data = json.loads(payment.extra_data)
    data = extra_data[-1] if isinstance(extra_data, list) else extra_data

    return_url = payment.return_url

    if not return_url:
        logger.warning(
            "Missing return_url for payment.",
            extra={"payment_id": payment_id, "checkout_pk": checkout_pk},
        )
        return HttpResponseNotFound(
            "Cannot perform payment. Lack of data about returnUrl."
        )

    try:
        request_data = prepare_api_request_data(request, data)
    except KeyError as e:
        return HttpResponseBadRequest(e.args[0])
    try:
        result = api_call(request_data, payment_details)
    except PaymentError as e:
        return HttpResponseBadRequest(str(e))
    handle_api_response(payment, checkout, result, channel_slug)
    redirect_url = prepare_redirect_url(payment_id, checkout_pk, result, return_url)
    return HttpResponseRedirectWithTrustedProtocol(redirect_url)


def prepare_api_request_data(request: WSGIRequest, data: dict):
    if "parameters" not in data or "payment_data" not in data:
        raise KeyError(
            "Cannot perform payment. Lack of payment data and parameters information."
        )

    params = data["parameters"]
    request_data: "QueryDict" = QueryDict("")

    if all([param in request.GET for param in params]):
        request_data = request.GET
    elif all([param in request.POST for param in params]):
        request_data = request.POST

    if not request_data:
        raise KeyError(
            "Cannot perform payment. Lack of required parameters in request."
        )

    api_request_data = {
        "paymentData": data["payment_data"],
        "details": {key: request_data[key] for key in params},
    }
    return api_request_data


def prepare_redirect_url(
    payment_id: str, checkout_pk: str, api_response: Adyen.Adyen, return_url: str
):
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)

    params = {
        "checkout": checkout_id,
        "payment": payment_id,
        "resultCode": api_response.message["resultCode"],
    }

    # Check if further action is needed.
    if "action" in api_response.message:
        params.update(api_response.message["action"])

    return prepare_url(urlencode(params), return_url)


def handle_api_response(
    payment: Payment,
    checkout: Optional[Checkout],
    response: Adyen.Adyen,
    channel_slug: str,
):
    payment_data = create_payment_information(
        payment=payment,
        payment_token=payment.token,
    )
    payment_brand = response.message.get("additionalData", {}).get("paymentMethod")
    if payment_brand:
        payment.cc_brand = payment_brand
        payment.save(update_fields=["cc_brand"])

    error_message = response.message.get("refusalReason")

    result_code = response.message["resultCode"].strip().lower()
    is_success = result_code not in FAILED_STATUSES

    action_required = False
    if "action" in response.message:
        action_required = True

    gateway_response = GatewayResponse(
        is_success=is_success,
        action_required=action_required,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment_data.amount,
        currency=payment_data.currency,
        transaction_id=response.message.get("pspReference", ""),
        error=error_message,
        raw_response=response.message,
        action_required_data=response.message.get("action"),
        psp_reference=response.message.get("pspReference", ""),
    )

    create_transaction(
        payment=payment,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        action_required=action_required,
        payment_information=payment_data,
        gateway_response=gateway_response,
    )
    if is_success and not action_required and not payment.order and checkout:
        manager = get_plugins_manager()

        confirm_payment_and_set_back_to_confirm(payment, manager, channel_slug)
        payment.refresh_from_db()  # refresh charge_status

        adyen_partial_payments = get_or_create_adyen_partial_payments(
            response.message, payment
        )

        create_order(payment, checkout, manager)

        if adyen_partial_payments:
            create_order_event_about_adyen_partial_payments(
                adyen_partial_payments, payment
            )


def confirm_payment_and_set_back_to_confirm(payment, manager, channel_slug):
    # The workaround for refund payments when something will crash in
    # `create_order` function before processing a payment.
    # At this moment we have a payment processed on Adyen side but we have to do
    # something more on Saleor side (ACTION_TO_CONFIRM), it's create an order in
    # this case, so before try to create the order we have to confirm the payment
    # and force change the flag to_confirm to True again.
    #
    # This is because we have to handle 2 flows:
    # 1. Having confirmed payment to refund easily when we can't create an order.
    # 2. Do not process payment again when `complete_checkout` logic will execute
    #    in `create_order` without errors. We just receive a processed transaction
    #    then.
    #
    # This fix is related to SALEOR-4777. PR #8471
    gateway.confirm(payment, manager, channel_slug)
    payment.to_confirm = True
    payment.save(update_fields=["to_confirm"])
