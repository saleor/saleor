import base64
import binascii
import hashlib
import hmac
import json
from typing import Any, Dict, Optional

from django.contrib.auth.hashers import check_password
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.http.request import HttpHeaders
from graphql_relay import from_global_id

from ....order.actions import (
    cancel_order,
    handle_fully_paid_order,
    order_authorized,
    order_captured,
    order_refunded,
)
from ....order.events import payment_gateway_notification_event
from ....payment.models import Payment, Transaction
from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse
from ...utils import create_transaction, gateway_postprocess
from .utils import convert_adyen_price_format


def get_payment(payment_id: str) -> Payment:
    _type, payment_id = from_global_id(payment_id)
    payment = Payment.objects.prefetch_related("order").filter(id=payment_id).first()
    return payment


def get_transaction(
    payment: "Payment", transaction_id: str, kind: TransactionKind,
) -> Transaction:
    transaction = payment.transactions.filter(kind=kind, token=transaction_id).first()
    return transaction


def create_new_transaction(notification, payment, kind):
    transaction_id = notification.get("pspReference")
    currency = notification.get("amount", {}).get("currency")
    amount = convert_adyen_price_format(
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
        raw_response={},
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

    payment_gateway_notification_event(
        order=payment.order, user=None, message=msg, payment=payment
    )


def handle_authorization(notification: Dict[str, Any], gateway_config: GatewayConfig):
    mark_capture = gateway_config.auto_capture
    if mark_capture:
        # If we mark order as a capture by default we don't need to handle auth actions
        return
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        # We don't know anything about that payment
        return

    transaction_id = notification.get("pspReference")
    transaction = get_transaction(payment, transaction_id, TransactionKind.AUTH)
    if transaction:
        # We already marked it as Auth
        return

    transaction = create_new_transaction(notification, payment, TransactionKind.AUTH)
    reason = notification.get("reason", "-")

    success_msg = f"Adyen: The payment  {transaction_id} request  was successful."
    failed_msg = f"Adyen: The payment {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, transaction.is_success
    )
    if payment.order:
        order_authorized(payment.order, None, transaction.amount, payment)


def handle_cancellation(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")
    transaction = get_transaction(payment, transaction_id, TransactionKind.CANCEL)
    if transaction:
        # it is already cancelled
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.CANCEL
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    success_msg = f"Adyen: The cancel {transaction_id} request was successful."
    failed_msg = f"Adyen: The camcel {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, new_transaction.is_success
    )
    if payment.order:
        cancel_order(payment.order, None)


def handle_cancel_or_refund(
    notification: Dict[str, Any], gateway_config: GatewayConfig
):
    additional_data = notification.get("additionalData")
    action = additional_data.get("modification.action")
    if action == "refund":
        handle_refund(notification, gateway_config)
    elif action == "cancel":
        handle_cancellation(notification, gateway_config)


def handle_capture(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    # FIXME execute order_fully_paid event
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")
    transaction = get_transaction(payment, transaction_id, TransactionKind.CAPTURE)
    if transaction and transaction.is_success:
        # it is already captured
        return

    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.CAPTURE
    )

    gateway_postprocess(new_transaction, payment)
    if payment.order:
        handle_fully_paid_order(payment.order)

    reason = notification.get("reason", "-")
    success_msg = f"Adyen: The capture {transaction_id} request was successful."
    failed_msg = f"Adyen: The capture {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, new_transaction.is_success
    )
    if payment.order:
        order_captured(payment.orderm, None, transaction.amount, payment)


def handle_failed_capture(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")

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
    mark_capture = gateway_config.auto_capture
    if mark_capture:
        # If we mark order as a capture by default we don't need to handle this action
        return
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")
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
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")
    transaction = get_transaction(payment, transaction_id, TransactionKind.REFUND)
    if transaction and transaction.is_success:
        # it is already refunded
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.REFUND
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    success_msg = f"Adyen: The refund {transaction_id} request was successful."
    failed_msg = f"Adyen: The refund {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, new_transaction.is_success
    )
    if payment.order:
        order_refunded(payment.order, None, transaction.amount, payment)


def handle_failed_refund(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")
    transaction = get_transaction(payment, transaction_id, TransactionKind.REFUND)
    if transaction and not transaction.is_success:
        # The refund is already saved
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.REFUND
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    msg = (
        f"Adyen: The refund {transaction_id} failed due to a technical issue. If you"
        f" receive more than two failures on the same refund, contact Adyen Support "
        f"Team. Reason: {reason}"
    )
    create_payment_notification_for_order(payment, msg, msg, new_transaction.is_success)


def handle_reversed_refund(
    notification: Dict[str, Any], _gateway_config: GatewayConfig
):
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")
    transaction = get_transaction(
        payment, transaction_id, TransactionKind.REFUND_REVERSED
    )

    if transaction and not transaction.is_success:
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
    notification: Dict[str, Any], _gateway_config: GatewayConfig
):

    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    transaction_id = notification.get("pspReference")
    transaction = get_transaction(payment, transaction_id, TransactionKind.REFUND)
    if transaction:
        # it is already refunded
        return
    new_transaction = create_new_transaction(
        notification, payment, TransactionKind.REFUND
    )
    gateway_postprocess(new_transaction, payment)

    reason = notification.get("reason", "-")
    success_msg = f"Adyen: The refund {transaction_id} request was successful."
    failed_msg = f"Adyen: The refund {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, new_transaction.is_success
    )
    if payment.order:
        order_refunded(payment.order, None, transaction.amount, payment)


def webhook_not_implemented(
    notification: Dict[str, Any], gateway_config: GatewayConfig
):
    adyen_id = notification.get("pspReference")
    success = notification.get("success", True)
    event = notification.get("eventCode")
    payment = get_payment(notification.get("merchantReference"))
    if not payment:
        return
    msg = (
        f"Received not implemented notification from Adyen. Event name: {event}, "
        f"success: {success}, adyen reference: {adyen_id}."
    )
    create_payment_notification_for_order(payment, msg, None, True)


EVENT_MAP = {
    "AUTHORISATION": handle_authorization,
    "AUTHORISATION_ADJUSTMENT": webhook_not_implemented,
    "CANCELLATION": handle_cancellation,
    "CANCEL_OR_REFUND": handle_cancel_or_refund,
    "CAPTURE": handle_capture,
    "CAPTURE_FAILED": handle_failed_capture,
    "HANDLED_EXTERNALLY": webhook_not_implemented,
    "ORDER_OPENED": webhook_not_implemented,
    "ORDER_CLOSED": webhook_not_implemented,
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

    """
    pspReference	7914073381342284
    originalReference
    merchantAccountCode	YOUR_MERCHANT_ACCOUNT
    merchantReference	TestPayment-1407325143704
    value	1130
    currency	EUR
    eventCode	AUTHORISATION
    success	true
    """
    hmac_key = gateway_config.connection_params.get("webhook_hmac")
    if not hmac_key:
        return True

    hmac_signature = notification.get("additionalData", {}).get("hmacSignature")
    if not hmac_signature and hmac_key:
        return False

    success = "true" if notification.get("success", "") else "false"
    if notification.get("success", None) is None:
        success = ""

    payload_list = [
        notification.get("pspReference", ""),
        notification.get("originalReference", ""),
        notification.get("merchantAccountCode", ""),
        notification.get("merchantReference", ""),
        notification.get("value", ""),
        notification.get("currency", ""),
        notification.get("eventCode", ""),
        success,
    ]
    payload = ":".join(payload_list)

    hm = hmac.new(hmac_key, payload.encode("utf-8"), hashlib.sha256)
    expected_merchant_sign = base64.b64encode(hm.digest())
    return hmac_signature == expected_merchant_sign.decode("utf-8")


def validate_auth_user(headers: HttpHeaders, gateway_config: "GatewayConfig") -> bool:
    username = gateway_config.connection_params["webhook_user"]
    password = gateway_config.connection_params["webhook_user_password"]
    auth_header = headers.get("Authorization")
    if not auth_header and not username:
        return True

    split_auth = auth_header.split(maxsplit=1)
    prefix = "BASIC"

    if len(split_auth) != 2 or split_auth[0].upper() != prefix:
        return False

    auth = split_auth[1]
    try:
        request_username, request_password = base64.b64decode(auth).split(":")
        user_is_correct = request_username == username
        if user_is_correct and check_password(request_password, password):
            return True
    except binascii.Error:
        pass
    return False


def handle_webhook(request: WSGIRequest, gateway_config: "GatewayConfig"):
    json_data = json.loads(request.body)
    # JSON and HTTP POST notifications always contain a single NotificationRequestItem
    # object.
    notification = json_data.get("notificationItems")[0].get(
        "NotificationRequestItem", {}
    )

    if not validate_hmac_signature(notification, gateway_config):
        return HttpResponseBadRequest("Invalid or missing hmac signature.")
    if not validate_auth_user(notification, gateway_config):
        return HttpResponseBadRequest("Invalid or missing basic auth.")

    event_handler = EVENT_MAP.get(notification.get("eventCode", ""))
    if event_handler:
        event_handler(notification, gateway_config)
        return HttpResponse("[accepted]")
    return HttpResponseNotFound()
