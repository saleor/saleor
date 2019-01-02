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
        payment: Dict, payment_token: str, amount: Decimal,
        **connection_params):
    auth_resp = authorize(payment, payment_token)
    if auth_resp['errors']:
        return auth_resp
    return capture(payment, payment_token, amount)


def authorize(payment: Dict, payment_token: str, **connection_params):
    success = dummy_success()
    error = None
    if not success:
        error = 'Unable to authorize transaction'
    return {
        'is_success': success,
        'transaction_id': payment_token,
        'gateway_response': {},
        'errors': error,
    }


def void(payment: Dict, payment_token: str, **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to void the transaction.'
    return {
        'is_success': success,
        'transaction_id': payment_token,
        'gateway_response': {},
        'errors': error,
    }


def capture(
        payment: Dict, payment_token: str, amount: Decimal,
        **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process capture'
    return {
        'is_success': success,
        'transaction_id': payment_token,
        'gateway_response': {},
        'errors': error,
    }


def refund(
        payment: Dict, payment_token: str, amount: Decimal,
        **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process refund'
    return {
        'is_success': success,
        'transaction_id': payment_token,
        'gateway_response': {},
        'errors': error,
    }


def charge(
        payment: Dict, payment_token: str, amount: Decimal,
        **connection_params):
    """Performs Authorize and Capture transactions in a single run."""
    auth_resp = authorize(payment, payment_token)
    if auth_resp['errors']:
        return auth_resp
    return capture(payment, payment_token, amount)
