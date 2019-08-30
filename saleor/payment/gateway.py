import logging

from django.core.exceptions import ImproperlyConfigured

from ..core.payments import Gateway, PaymentInterface
from ..extensions.manager import get_extensions_manager

from . import GatewayError, TransactionKind, PaymentError
from .models import Payment, Transaction
from .utils import (
    create_payment_information,
    create_transaction,
    validate_gateway_response,
    _gateway_postprocess,
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


class PaymentGateway:
    def __init__(self):
        self.plugin_manager: PaymentInterface = get_extensions_manager()

    @raise_payment_error
    @payment_postprocess
    def process_payment(
        self, payment: Payment, token: str, store_source: bool = False
    ) -> Transaction:
        payment_data = create_payment_information(
            payment=payment, payment_token=token, store_source=store_source
        )
        gateway = _get_gateway(payment)
        response, error = _fetch_gateway_response(
            self.plugin_manager.process_payment, gateway, payment_data
        )
        txn = create_transaction(
            payment=payment,
            kind=TransactionKind.CAPTURE,
            payment_information=payment_data,
            error_msg=error,
            gateway_response=response,
        )
        return txn


def _get_gateway(payment: Payment) -> Gateway:
    try:
        gateway = Gateway(payment.gateway)
    except AttributeError:
        raise ImproperlyConfigured("Payment gateway %s is not configured." % gateway)

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
