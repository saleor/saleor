import base64
import binascii
import hashlib
import hmac
import json
import logging
from json.decoder import JSONDecodeError
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlencode, urlparse

import Adyen
import graphene
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    QueryDict,
)
from django.http.request import HttpHeaders
from django.http.response import HttpResponseRedirect
from graphql_relay import from_global_id

from ....checkout.complete_checkout import complete_checkout
from ....checkout.models import Checkout
from ....checkout.utils import fetch_checkout_lines
from ....core.transactions import transaction_with_commit_on_errors
from ....core.utils.url import prepare_url
from ....discount.utils import fetch_active_discounts
from ....order.actions import (
    cancel_order,
    order_authorized,
    order_captured,
    order_refunded,
)
from ....order.events import external_notification_event
from ....payment.models import Payment, Transaction
from ....plugins.manager import get_plugins_manager
from ... import ChargeStatus, PaymentError, TransactionKind
from ...gateway import payment_refund_or_void
from ...interface import GatewayConfig, GatewayResponse
from ...utils import create_payment_information, create_transaction, gateway_postprocess
from .utils.common import FAILED_STATUSES, api_call, from_adyen_price

logger = logging.getLogger(__name__)


def get_payment(
    payment_id: Optional[str],
    transaction_id: Optional[str] = None,
    check_if_active=True,
) -> Optional[Payment]:
    transaction_id = transaction_id or ""
    if payment_id is None or not payment_id.strip():
        logger.warning("Missing payment ID. Reference %s", transaction_id)
        return None
    try:
        _type, db_payment_id = from_global_id(payment_id)
    except (UnicodeDecodeError, binascii.Error):
        logger.warning(
            "Unable to decode the payment ID %s. Reference %s",
            payment_id,
            transaction_id,
        )
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


def get_checkout(payment: Payment) -> Optional[Checkout]:
    if not payment.checkout:
        return None
    # Lock checkout in the same way as in checkoutComplete
    return (
        Checkout.objects.select_for_update(of=("self",))
        .prefetch_related(
            "gift_cards",
            "lines__variant__product",
        )
        .select_related("shipping_method__shipping_zone")
        .filter(pk=payment.checkout.pk)
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
    amount = from_adyen_price(notification.get("amount", {}).get("value"), currency)
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
        searchable_key=transaction_id,
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
        message=msg,
        parameters={"service": payment.gateway, "id": payment.token},
    )


def create_order(payment, checkout):
    manager = get_plugins_manager()
    try:
        discounts = fetch_active_discounts()
        lines = fetch_checkout_lines(checkout)
        order, _, _ = complete_checkout(
            manager=manager,
            checkout=checkout,
            lines=lines,
            payment_data={},
            store_source=False,
            discounts=discounts,
            user=checkout.user or AnonymousUser(),
        )
    except ValidationError:
        payment_refund_or_void(payment)
        return None
    # Refresh the payment to assign the newly created order
    payment.refresh_from_db()
    return order


def handle_not_created_order(notification, payment, checkout, kind):
    """Process the notification in case when payment doesn't have assigned order."""

    # We don't want to create order for payment that is cancelled or refunded
    if payment.charge_status not in {
        ChargeStatus.NOT_CHARGED,
        ChargeStatus.PENDING,
        ChargeStatus.PARTIALLY_CHARGED,
        ChargeStatus.FULLY_CHARGED,
    }:
        return
    transaction = payment.transactions.filter(
        action_required=False, is_success=True, kind=kind
    ).last()
    if not transaction:
        # If the payment is not Auth/Capture, it means that user didn't return to the
        # storefront and we need to finalize the checkout asynchronously.
        transaction = create_new_transaction(
            notification, payment, TransactionKind.ACTION_TO_CONFIRM
        )

    # Only when we confirm that notification is success we will create the order
    if transaction.is_success and checkout:  # type: ignore
        order = create_order(payment, checkout)
        return order
    return None


def handle_authorization(notification: Dict[str, Any], gateway_config: GatewayConfig):
    transaction_id = notification.get("pspReference")
    payment = get_payment(notification.get("merchantReference"), transaction_id)
    if not payment:
        # We don't know anything about that payment
        return
    checkout = get_checkout(payment)

    adyen_auto_capture = gateway_config.connection_params["adyen_auto_capture"]
    kind = TransactionKind.AUTH
    if adyen_auto_capture:
        kind = TransactionKind.CAPTURE
    if not payment.order:
        handle_not_created_order(notification, payment, checkout, kind)
    else:
        adyen_auto_capture = gateway_config.connection_params["adyen_auto_capture"]
        kind = TransactionKind.AUTH
        if adyen_auto_capture:
            kind = TransactionKind.CAPTURE
        transaction = payment.transactions.filter(
            token=transaction_id,
            action_required=False,
            is_success=True,
            kind__in=[TransactionKind.AUTH, TransactionKind.CAPTURE],
        ).last()
        if not transaction:
            new_transaction = create_new_transaction(notification, payment, kind)
            if new_transaction.is_success:
                gateway_postprocess(new_transaction, payment)
                if adyen_auto_capture:
                    order_captured(payment.order, None, new_transaction.amount, payment)
                else:
                    order_authorized(
                        payment.order, None, new_transaction.amount, payment
                    )
    reason = notification.get("reason", "-")
    is_success = True if notification.get("success") == "true" else False
    success_msg = f"Adyen: The payment  {transaction_id} request  was successful."
    failed_msg = (
        f"Adyen: The payment {transaction_id} request failed. Reason: {reason}."
    )
    create_payment_notification_for_order(payment, success_msg, failed_msg, is_success)


def handle_cancellation(notification: Dict[str, Any], _gateway_config: GatewayConfig):
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
    failed_msg = f"Adyen: The camcel {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(
        payment, success_msg, failed_msg, new_transaction.is_success
    )
    if payment.order and new_transaction.is_success:
        cancel_order(payment.order, None)


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
    payment = get_payment(notification.get("merchantReference"), transaction_id)
    if not payment:
        return
    checkout = get_checkout(payment)

    if not payment.order:
        handle_not_created_order(
            notification, payment, checkout, TransactionKind.CAPTURE
        )
    else:
        capture_transaction = payment.transactions.filter(
            action_required=False,
            is_success=True,
            kind=TransactionKind.CAPTURE,
        ).last()
        new_transaction = create_new_transaction(
            notification, payment, TransactionKind.CAPTURE
        )
        if new_transaction.is_success and not capture_transaction:
            gateway_postprocess(new_transaction, payment)
            order_captured(payment.order, None, new_transaction.amount, payment)

    reason = notification.get("reason", "-")
    is_success = True if notification.get("success") == "true" else False
    success_msg = f"Adyen: The capture {transaction_id} request was successful."
    failed_msg = f"Adyen: The capture {transaction_id} request failed. Reason: {reason}"
    create_payment_notification_for_order(payment, success_msg, failed_msg, is_success)


def handle_failed_capture(notification: Dict[str, Any], _gateway_config: GatewayConfig):
    # https://docs.adyen.com/checkout/capture#failed-capture
    transaction_id = notification.get("pspReference")
    payment = get_payment(notification.get("merchantReference"), transaction_id)
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
    payment = get_payment(notification.get("merchantReference"), transaction_id)
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
    payment = get_payment(notification.get("merchantReference"), transaction_id)
    if not payment:
        return
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
    if payment.order and new_transaction.is_success:
        order_refunded(payment.order, None, new_transaction.amount, payment)


def _get_kind(transaction: Optional[Transaction]) -> str:
    if transaction:
        return transaction.kind
    # To proceed the refund we already need to have the capture status so we will use it
    return TransactionKind.CAPTURE


def handle_failed_refund(notification: Dict[str, Any], gateway_config: GatewayConfig):
    # https://docs.adyen.com/checkout/refund#failed-refund
    transaction_id = notification.get("pspReference")
    payment = get_payment(notification.get("merchantReference"), transaction_id)
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
    payment = get_payment(notification.get("merchantReference"), transaction_id)
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
    hmac_signature: Optional[str] = notification.get("additionalData", {}).get(
        "hmacSignature"
    )
    hmac_key: Optional[str] = gateway_config.connection_params.get("webhook_hmac")
    if not hmac_key and not hmac_signature:
        return True

    if not hmac_key and hmac_signature:
        return False

    if not hmac_signature and hmac_key:
        return False

    hmac_key = hmac_key.encode()  # type: ignore

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
    return hmac_signature == expected_merchant_sign.decode("utf-8")


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


@transaction_with_commit_on_errors()
def handle_additional_actions(
    request: WSGIRequest,
    payment_details: Callable,
):
    payment_id = request.GET.get("payment")
    checkout_pk = request.GET.get("checkout")

    if not payment_id or not checkout_pk:
        return HttpResponseNotFound()

    payment = get_payment(payment_id, transaction_id=None)
    if not payment:
        return HttpResponseNotFound(
            "Cannot perform payment.There is no active adyen payment."
        )
    if not payment.checkout or str(payment.checkout.token) != checkout_pk:
        return HttpResponseNotFound(
            "Cannot perform payment.There is no checkout with this payment."
        )

    extra_data = json.loads(payment.extra_data)
    data = extra_data[-1] if isinstance(extra_data, list) else extra_data

    return_url = payment.return_url

    if not return_url:
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
    handle_api_response(payment, result)
    redirect_url = prepare_redirect_url(payment_id, checkout_pk, result, return_url)
    parsed = urlparse(return_url)
    redirect_class = HttpResponseRedirect
    redirect_class.allowed_schemes = [parsed.scheme]
    return redirect_class(redirect_url)


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
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)  # type: ignore

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
    response: Adyen.Adyen,
):
    checkout = get_checkout(payment)
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
        searchable_key=response.message.get("pspReference", ""),
    )

    create_transaction(
        payment=payment,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        action_required=action_required,
        payment_information=payment_data,
        gateway_response=gateway_response,
    )
    if is_success and not action_required and not payment.order:
        create_order(payment, checkout)
