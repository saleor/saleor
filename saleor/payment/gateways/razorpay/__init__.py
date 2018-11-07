import logging
import uuid
from decimal import Decimal
from typing import Dict, Tuple

from django.utils.translation import pgettext_lazy

import razorpay
from razorpay import errors

from ... import TransactionKind
from ...models import Payment, Transaction
from ...utils import create_transaction
from .forms import RazorPaymentForm
from .utils import get_amount_for_razorpay, get_error_response

# Define the existing error messages as lazy `pgettext`.
ERROR_MSG_ORDER_NOT_CHARGED = pgettext_lazy(
    'Razorpay payment error', 'Order was not charged.')
ERROR_MSG_INVALID_REQUEST = pgettext_lazy(
    'Razorpay payment error', 'The payment data was invalid.')
ERROR_MSG_SERVER_ERROR = pgettext_lazy(
    'Razorpay payment error', 'The order couldn\'t be proceeded.')
ERROR_UNSUPPORTED_CURRENCY = pgettext_lazy(
    'Razorpay payment error', 'The %(currency)s currency is not supported.')

# The list of currencies supported by razorpay
SUPPORTED_CURRENCIES = 'INR',

# Define what are the razorpay exceptions,
# as the razorpay provider doesn't define a base exception as of now.
RAZORPAY_EXCEPTIONS = (
    errors.BadRequestError, errors.GatewayError, errors.ServerError)

# Get the logger for this file, it will allow us to log
# error responses from razorpay.
logger = logging.getLogger(__name__)


def _generate_transaction(
        payment: Payment,
        kind: str,
        amount: Decimal,
        *,
        id='',
        is_success=True,
        **data) -> Transaction:
    """Creates a transaction from a Razorpay's success payload
    or from passed data."""
    transaction = create_transaction(
        payment=payment,
        kind=kind,
        amount=amount,
        currency=data.pop('currency', payment.currency),
        gateway_response=data,
        token=id,
        is_success=is_success)
    return transaction


def check_payment_supported(payment: Payment):
    """Checks that a given payment is supported"""
    if payment.currency not in SUPPORTED_CURRENCIES:
        return ERROR_UNSUPPORTED_CURRENCY % {
            'currency': payment.currency}


def get_error_message_from_razorpay_error(exc: BaseException):
    """Convert a error razorpay error to a user friendly error message
    and log the exception to stderr."""
    logger.exception(exc)
    if isinstance(exc, errors.BadRequestError):
        return ERROR_MSG_INVALID_REQUEST
    else:
        return ERROR_MSG_SERVER_ERROR


def clean_razorpay_response(response: dict):
    """As the Razorpay response payload contains the final amount
    as an integer, we converts it to a decimal object (by dividing by 100)."""
    response['amount'] = Decimal(response['amount']) / 100


def get_form_class():
    """Return the associated razorpay payment form."""
    return RazorPaymentForm


def get_client(public_key: str, secret_key: str, **_):
    """Create a Razorpay client from set-up application keys."""
    razorpay_client = razorpay.Client(auth=(public_key, secret_key))
    return razorpay_client


def get_client_token(**_):
    """Generate a random client token."""
    return str(uuid.uuid4())


def charge(
        payment: Payment,
        payment_token: str,
        amount: Decimal,
        **connection_params: Dict) -> Tuple[Transaction, str]:
    """Charge a authorized payment using the razorpay client.

    But it first check if the given payment instance is supported
    by the gateway.

    If an error from razorpay occurs,
    we flag the transaction as failed and return
    a short user friendly description of the error
    after logging the error to stderr."""
    error = check_payment_supported(payment=payment)
    razorpay_client = get_client(**connection_params)
    razorpay_amount = get_amount_for_razorpay(amount)

    if not error:
        try:
            response = razorpay_client.payment.capture(
                payment_token, razorpay_amount)
            clean_razorpay_response(response)
        except RAZORPAY_EXCEPTIONS as exc:
            error = get_error_message_from_razorpay_error(exc)
            response = get_error_response(amount, id=payment_token)
    else:
        response = get_error_response(amount, id=payment_token)

    transaction = _generate_transaction(
        payment=payment, kind=TransactionKind.CHARGE, **response)
    return transaction, error


def refund(payment: Payment, amount: Decimal, **connection_params):
    """Refund a payment using the razorpay client.

    But it first check if the given payment instance is supported
    by the gateway.

    It first retrieve a `charge` transaction to retrieve the
    payment id to refund. And return an error with a failed transaction
    if the there is no such transaction, or if an error
    from razorpay occurs during the refund."""
    error = check_payment_supported(payment=payment)
    capture_txn = payment.transactions.filter(
        kind=TransactionKind.CHARGE, is_success=True).first()

    if error:
        response = get_error_response(amount)
    elif capture_txn is not None:
        razorpay_client = get_client(**connection_params)
        razorpay_amount = get_amount_for_razorpay(amount)
        try:
            response = razorpay_client.payment.refund(
                capture_txn.token, razorpay_amount)
            clean_razorpay_response(response)
        except RAZORPAY_EXCEPTIONS as exc:
            error = get_error_message_from_razorpay_error(exc)
            response = get_error_response(amount)
    else:
        error = ERROR_MSG_ORDER_NOT_CHARGED
        response = get_error_response(amount)

    transaction = _generate_transaction(
        payment=payment, kind=TransactionKind.REFUND, **response)
    return transaction, error
