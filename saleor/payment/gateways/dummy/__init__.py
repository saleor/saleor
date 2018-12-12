import uuid
from decimal import Decimal
from typing import Dict

from django.conf import settings
from prices import Money

from ... import TransactionKind
from ...models import Payment
from ...utils import create_transaction
from .forms import DummyPaymentForm


def dummy_success():
    return True


def get_client_token(**connection_params):
    return str(uuid.uuid4())


def get_template():
    return 'order/payment/dummy.html'


def get_form_class():
    return DummyPaymentForm


def process_payment(
        payment: Payment, payment_token: str, amount: Decimal,
        **connection_params):
    authorize(payment_token)
    capture_success, capture_response, capture_errors = capture(
        payment, payment_token)

    return capture_success, capture_response, capture_errors


def authorize(payment: Payment, payment_token: str, **connection_params):
    success = dummy_success()
    error = None
    if not success:
        error = 'Unable to authorize transaction'
    return success, {}, error


def void(payment: Payment, **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to void the transaction.'
    return success, {}, error


def capture(payment: Payment, amount: Decimal, **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process capture'
    return success, {}, error


def refund(payment: Payment, amount: Decimal, **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process refund'
    return success, {}, error


def charge(
        payment: Payment, payment_token: str, amount: Decimal,
        **connection_params):
    """Performs Authorize and Capture transactions in a single run."""
    is_success, response, error = authorize(payment, payment_token)
    if error:
        return is_success, response, error
    return capture(payment, amount)
