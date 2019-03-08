import logging
import uuid
from decimal import Decimal
from typing import Dict

import razorpay
import razorpay.errors

from . import errors
from .forms import RazorPaymentForm
from .utils import get_amount_for_razorpay, get_error_response

TEMPLATE_PATH = 'order/payment/razorpay.html'

# The list of currencies supported by razorpay
SUPPORTED_CURRENCIES = 'INR',

# Define what are the razorpay exceptions,
# as the razorpay provider doesn't define a base exception as of now.
RAZORPAY_EXCEPTIONS = (
    razorpay.errors.BadRequestError,
    razorpay.errors.GatewayError,
    razorpay.errors.ServerError)

# Get the logger for this file, it will allow us to log
# error responses from razorpay.
logger = logging.getLogger(__name__)


class TransactionKind:
    AUTH = 'auth'
    CAPTURE = 'capture'
    CHARGE = 'charge'
    REFUND = 'refund'
    VOID = 'void'


def _generate_response(
        payment_information: Dict, kind: str, data: Dict) -> Dict:
    """Generate Saleor transaction information from
    Razorpay's success payload or from passed data."""
    return {
        'transaction_id': data.get('id', payment_information['token']),
        'kind': kind,
        'amount': data.get('amount', payment_information['amount']),
        'currency': data.get('currency', payment_information['currency']),
        'error': data.get('error', None),
        'is_success': data.get('is_success', True),
        'raw_response': data}


def check_payment_supported(payment_information: Dict):
    """Checks that a given payment is supported."""
    if payment_information['currency'] not in SUPPORTED_CURRENCIES:
        return errors.UNSUPPORTED_CURRENCY % {
            'currency': payment_information['currency']}


def get_error_message_from_razorpay_error(exc: BaseException):
    """Convert a error razorpay error to a user friendly error message
    and log the exception to stderr."""
    logger.exception(exc)
    if isinstance(exc, razorpay.errors.BadRequestError):
        return errors.INVALID_REQUEST
    else:
        return errors.SERVER_ERROR


def clean_razorpay_response(response: dict):
    """As the Razorpay response payload contains the final amount
    in Indian rupees, we convert the amount to paisa (by dividing by 100)."""
    response['amount'] = Decimal(response['amount']) / 100


def create_form(data, payment_information, connection_params):
    """Return the associated razorpay payment form."""
    return RazorPaymentForm(
        data=data, payment_information=payment_information,
        connection_params=connection_params,
    )


def get_client(public_key: str, secret_key: str, **_):
    """Create a Razorpay client from set-up application keys."""
    razorpay_client = razorpay.Client(auth=(public_key, secret_key))
    return razorpay_client


def get_client_token(**_):
    """Generate a random client token."""
    return str(uuid.uuid4())


def charge(payment_information: Dict, connection_params: Dict) -> Dict:
    """Charge a authorized payment using the razorpay client.

    But it first check if the given payment instance is supported
    by the gateway.

    If an error from razorpay occurs,
    we flag the transaction as failed and return
    a short user friendly description of the error
    after logging the error to stderr."""
    error = check_payment_supported(payment_information=payment_information)
    razorpay_client = get_client(**connection_params)
    razorpay_amount = get_amount_for_razorpay(payment_information['amount'])

    if not error:
        try:
            response = razorpay_client.payment.capture(
                payment_information['token'], razorpay_amount)
            clean_razorpay_response(response)
        except RAZORPAY_EXCEPTIONS as exc:
            error = get_error_message_from_razorpay_error(exc)
            response = get_error_response(
                payment_information['amount'], error=error,
                id=payment_information['token'])
    else:
        response = get_error_response(
            payment_information['amount'], error=error,
            id=payment_information['token'])

    return _generate_response(
        payment_information=payment_information,
        kind=TransactionKind.CHARGE, data=response)


def refund(payment_information: Dict, connection_params) -> Dict:
    """Refund a payment using the razorpay client.

    But it first check if the given payment instance is supported
    by the gateway.

    It first retrieve a `charge` transaction to retrieve the
    payment id to refund. And return an error with a failed transaction
    if the there is no such transaction, or if an error
    from razorpay occurs during the refund."""
    error = check_payment_supported(payment_information=payment_information)

    if error:
        response = get_error_response(
            payment_information['amount'], error=error)
    else:
        razorpay_client = get_client(**connection_params)
        razorpay_amount = get_amount_for_razorpay(
            payment_information['amount'])
        try:
            response = razorpay_client.payment.refund(
                payment_information['token'], razorpay_amount)
            clean_razorpay_response(response)
        except RAZORPAY_EXCEPTIONS as exc:
            error = get_error_message_from_razorpay_error(exc)
            response = get_error_response(
                payment_information['amount'], error=error)

    return _generate_response(
        payment_information=payment_information,
        kind=TransactionKind.REFUND, data=response)


def process_payment(payment_information: Dict, connection_params) -> Dict:
    return charge(
        payment_information=payment_information,
        connection_params=connection_params)
