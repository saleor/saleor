import logging
from decimal import Decimal

from django.core.exceptions import ImproperlyConfigured

from ..core.payments import Gateway
from ..extensions.manager import get_extensions_manager
from . import GatewayError, PaymentError, TransactionKind
from .models import Payment, Transaction
from .utils import (
    _gateway_postprocess,
    clean_authorize,
    clean_capture,
    create_payment_information,
    create_transaction,
    validate_gateway_response,
)

logger = logging.getLogger(__name__)
ERROR_MSG = "Oops! Something went wrong."
GENERIC_TRANSACTION_ERROR = "Transaction was unsuccessful"


def raise_payment_error(fn):
    def wrapped(*args, **kwargs):
        result = fn(*args, **kwargs)
        if not result.is_success:
            raise PaymentError(result.error or GENERIC_TRANSACTION_ERROR)
        return result

    return wrapped


def payment_postprocess(fn):
    def wrapped(*args, **kwargs):
        txn = fn(*args, **kwargs)
        _gateway_postprocess(txn, txn.payment)
        return txn

    return wrapped


def require_active_payment(fn):
    def wrapped(payment: Payment, *args, **kwargs):
        if not payment.is_active:
            raise PaymentError("This payment is no longer active.")
        return fn(payment, *args, **kwargs)

    return wrapped


@raise_payment_error
@payment_postprocess
@require_active_payment
def process_payment(
    payment: Payment, token: str, store_source: bool = False
) -> Transaction:
    plugin_manager = get_extensions_manager()
    gateway = _get_gateway(payment)
    payment_data = create_payment_information(
        payment=payment, payment_token=token, store_source=store_source
    )
    response, error = _fetch_gateway_response(
        plugin_manager.process_payment, gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.CAPTURE,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@payment_postprocess
def authorize(
    payment: Payment, token: str, store_source: bool = False
) -> Transaction:
    plugin_manager = get_extensions_manager()
    clean_authorize(payment)
    gateway = _get_gateway(payment)
    payment_data = create_payment_information(
        payment=payment, payment_token=token, store_source=store_source
    )
    response, error = _fetch_gateway_response(
        plugin_manager.authorize_payment, gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.AUTH,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@payment_postprocess
def capture(
    payment: Payment, amount: Decimal = None, store_source: bool = False
) -> Transaction:
    plugin_manager = get_extensions_manager()
    if amount is None:
        amount = payment.get_charge_amount()
    clean_capture(payment, amount)
    gateway = _get_gateway(payment)
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(
        payment=payment,
        payment_token=token,
        amount=amount,
        store_source=store_source,
    )
    response, error = _fetch_gateway_response(
        plugin_manager.capture_payment, gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.CAPTURE,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@payment_postprocess
def refund(payment: Payment, amount: Decimal = None) -> Transaction:
    plugin_manager = get_extensions_manager()
    if amount is None:
        amount = payment.captured_amount
    _validate_refund_amound(payment, amount)
    if not payment.can_refund():
        raise PaymentError("This payment cannot be refunded.")
    gateway = _get_gateway(payment)
    token = _get_past_transaction_token(payment, TransactionKind.CAPTURE)
    payment_data = create_payment_information(
        payment=payment, payment_token=token, amount=amount
    )
    response, error = _fetch_gateway_response(
        plugin_manager.refund_payment, gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.REFUND,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@payment_postprocess
@require_active_payment
def void(payment: Payment) -> Transaction:
    plugin_manager = get_extensions_manager()
    gateway = _get_gateway(payment)
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(payment=payment, payment_token=token)
    response, error = _fetch_gateway_response(
        plugin_manager.void_payment, gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.VOID,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@payment_postprocess
@require_active_payment
def confirm(payment: Payment) -> Transaction:
    plugin_manager = get_extensions_manager()
    gateway = _get_gateway(payment)
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(payment=payment, payment_token=token)
    response, error = _fetch_gateway_response(
        plugin_manager.confirm_payment, gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.CONFIRM,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


def _get_gateway(payment: Payment) -> Gateway:
    try:
        gateway = Gateway(payment.gateway)
    except AttributeError:
        raise ImproperlyConfigured(f"Payment gateway {gateway} is not configured.")

    return gateway


def _fetch_gateway_response(fn, *args, **kwargs):
    response, error = None, None
    try:
        response = fn(*args, **kwargs)
        validate_gateway_response(response)
    except GatewayError:
        logger.exception("Gateway reponse validation failed!")
        response = None
        error = ERROR_MSG
    except Exception:
        logger.exception("Error encountered while executing payment gateway.")
        error = ERROR_MSG
        response = None
    return response, error


def _get_past_transaction_token(payment: Payment, kind: TransactionKind):
    txn = payment.transactions.filter(kind=kind, is_success=True).first()
    if txn is None:
        raise PaymentError("Cannot find successful {kind.value} transaction")
    return txn.token


def _validate_refund_amound(payment: Payment, amount: Decimal):
    if amount <= 0:
        raise PaymentError("Amount should be a positive number.")
    if amount > payment.captured_amount:
        raise PaymentError("Cannot refund more than captured")
