import uuid
from decimal import Decimal
from typing import Dict

from django.conf import settings
from prices import Money

from .forms import DummyPaymentForm


def dummy_success():
    return True


def get_client_token(**connection_params):
    return str(uuid.uuid4())


def get_template():
    return 'order/payment/dummy.html'


def get_form_class():
    return DummyPaymentForm


def process_payment(payment_information: Dict, **connection_params) -> Dict:
    """Process the whole payment, by calling authorize and capture."""
    auth_resp = authorize(payment_information, **connection_params)
    if auth_resp['error']:
        return auth_resp
    return [auth_resp, capture(payment_information, **connection_params)]


def authorize(payment_information: Dict, **connection_params) -> Dict:
    success = dummy_success()
    error = None
    if not success:
        error = 'Unable to authorize transaction'
    return {
        'is_success': success,
        'kind': 'auth',
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def void(payment_information: Dict, **connection_params) -> Dict:
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to void the transaction.'
    return {
        'is_success': success,
        'kind': 'void',
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def capture(payment_information: Dict, **connection_params: Dict) -> Dict:
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process capture'
    return {
        'is_success': success,
        'kind': 'capture',
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def refund(payment_information: Dict, **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process refund'
    return {
        'is_success': success,
        'kind': 'refund',
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def charge(payment_information: Dict, **connection_params):
    """Performs Authorize and Capture transactions in a single run."""
    auth_resp = authorize(payment_information, **connection_params)
    if auth_resp['error']:
        return auth_resp
    return [auth_resp, capture(payment_information, **connection_params)]
