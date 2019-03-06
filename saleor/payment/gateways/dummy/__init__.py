import uuid
from typing import Dict

from ... import ChargeStatus
from .forms import DummyPaymentForm

TEMPLATE_PATH = 'order/payment/dummy.html'


class TransactionKind:
    AUTH = 'auth'
    CAPTURE = 'capture'
    CHARGE = 'charge'
    REFUND = 'refund'
    VOID = 'void'


def dummy_success():
    return True


def get_client_token(**_):
    return str(uuid.uuid4())


def create_form(data, payment_information, connection_params):
    return DummyPaymentForm(data=data)


def authorize(payment_information: Dict, connection_params) -> Dict:
    success = dummy_success()
    error = None
    if not success:
        error = 'Unable to authorize transaction'
    return {
        'is_success': success,
        'kind': TransactionKind.AUTH,
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def void(payment_information: Dict, connection_params) -> Dict:
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to void the transaction.'
    return {
        'is_success': success,
        'kind': TransactionKind.VOID,
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def capture(payment_information: Dict, connection_params: Dict) -> Dict:
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process capture'
    return {
        'is_success': success,
        'kind': TransactionKind.CAPTURE,
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def refund(payment_information: Dict, connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process refund'
    return {
        'is_success': success,
        'kind': TransactionKind.REFUND,
        'amount': payment_information['amount'],
        'currency': payment_information['currency'],
        'transaction_id': payment_information['token'],
        'error': error}


def charge(payment_information: Dict, connection_params):
    """Performs Authorize and Capture transactions in a single run."""
    auth_resp = authorize(payment_information, connection_params)
    if not auth_resp['is_success']:
        return auth_resp
    return [auth_resp, capture(payment_information, connection_params)]


def process_payment(payment_information: Dict, connection_params) -> Dict:
    """Process the payment."""
    token = payment_information.get('token')

    # Process payment normally if payment token is valid
    if token not in dict(ChargeStatus.CHOICES):
        return charge(payment_information, connection_params)

    # Process payment by charge status which is selected in the payment form
    # Note that is for testing by dummy gateway only
    charge_status = token
    responses = [authorize(payment_information, connection_params)]
    if charge_status == ChargeStatus.NOT_CHARGED:
        return responses

    responses.append(capture(payment_information, connection_params))
    if charge_status == ChargeStatus.FULLY_REFUNDED:
        responses.append(refund(payment_information, connection_params))
    return responses
