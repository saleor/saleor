import logging
from decimal import Decimal
from typing import List

from django import forms

from ..extensions.manager import get_extensions_manager
from ..payment.interface import TokenConfig
from . import GatewayError, PaymentError, TransactionKind
from .models import Payment, Transaction
from .utils import (
    clean_authorize,
    clean_capture,
    create_payment_information,
    create_transaction,
    gateway_postprocess,
    update_card_details,
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
        gateway_postprocess(txn, txn.payment)
        return txn

    return wrapped


def require_active_payment(fn):
    def wrapped(payment: Payment, *args, **kwargs):
        if not payment.is_active:
            raise PaymentError("This payment is no longer active.")
        return fn(payment, *args, **kwargs)

    return wrapped


@payment_postprocess
@raise_payment_error
@require_active_payment
def process_payment(
    payment: Payment, token: str, store_source: bool = False
) -> Transaction:
    plugin_manager = get_extensions_manager()
    payment_data = create_payment_information(
        payment=payment, payment_token=token, store_source=store_source
    )
    response, error = _fetch_gateway_response(
        plugin_manager.process_payment, payment.gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.CAPTURE,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@payment_postprocess
@raise_payment_error
@require_active_payment
def authorize(payment: Payment, token: str, store_source: bool = False) -> Transaction:
    plugin_manager = get_extensions_manager()
    clean_authorize(payment)
    payment_data = create_payment_information(
        payment=payment, payment_token=token, store_source=store_source
    )
    response, error = _fetch_gateway_response(
        plugin_manager.authorize_payment, payment.gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.AUTH,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@payment_postprocess
@raise_payment_error
@require_active_payment
def capture(
    payment: Payment, amount: Decimal = None, store_source: bool = False
) -> Transaction:
    plugin_manager = get_extensions_manager()
    if amount is None:
        amount = payment.get_charge_amount()
    clean_capture(payment, Decimal(amount))
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(
        payment=payment, payment_token=token, amount=amount, store_source=store_source
    )
    response, error = _fetch_gateway_response(
        plugin_manager.capture_payment, payment.gateway, payment_data
    )
    if response.card_info:
        update_card_details(payment, response)
    return create_transaction(
        payment=payment,
        kind=TransactionKind.CAPTURE,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@payment_postprocess
@raise_payment_error
@require_active_payment
def refund(payment: Payment, amount: Decimal = None) -> Transaction:
    plugin_manager = get_extensions_manager()
    if amount is None:
        amount = payment.captured_amount
    _validate_refund_amound(payment, amount)
    if not payment.can_refund():
        raise PaymentError("This payment cannot be refunded.")
    token = _get_past_transaction_token(payment, TransactionKind.CAPTURE)
    payment_data = create_payment_information(
        payment=payment, payment_token=token, amount=amount
    )
    response, error = _fetch_gateway_response(
        plugin_manager.refund_payment, payment.gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.REFUND,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@payment_postprocess
@raise_payment_error
@require_active_payment
def void(payment: Payment) -> Transaction:
    plugin_manager = get_extensions_manager()
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(payment=payment, payment_token=token)
    response, error = _fetch_gateway_response(
        plugin_manager.void_payment, payment.gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.VOID,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@payment_postprocess
@raise_payment_error
@require_active_payment
def confirm(payment: Payment) -> Transaction:
    plugin_manager = get_extensions_manager()
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(payment=payment, payment_token=token)
    response, error = _fetch_gateway_response(
        plugin_manager.confirm_payment, payment.gateway, payment_data
    )
    return create_transaction(
        payment=payment,
        kind=TransactionKind.CONFIRM,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@require_active_payment
def create_payment_form(payment: Payment, data) -> forms.Form:
    plugin_manager = get_extensions_manager()
    payment_data = create_payment_information(payment)
    return plugin_manager.create_payment_form(data, payment.gateway, payment_data)


def list_payment_sources(gateway: str, customer_id: str) -> List["CustomerSource"]:
    plugin_manager = get_extensions_manager()
    return plugin_manager.list_payment_sources(gateway, customer_id)


def get_client_token(gateway: str, customer_id: str = None) -> str:
    plugin_manager = get_extensions_manager()
    token_config = TokenConfig(customer_id=customer_id)
    return plugin_manager.get_client_token(gateway, token_config)


def list_gateways() -> List[dict]:
    return get_extensions_manager().list_payment_gateways()


def get_template_path(gateway: str) -> str:
    return get_extensions_manager().get_payment_template(gateway)


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
        raise PaymentError(f"Cannot find successful {kind} transaction")
    return txn.token


def _validate_refund_amound(payment: Payment, amount: Decimal):
    if amount <= 0:
        raise PaymentError("Amount should be a positive number.")
    if amount > payment.captured_amount:
        raise PaymentError("Cannot refund more than captured")
