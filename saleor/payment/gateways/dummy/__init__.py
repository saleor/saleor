import uuid
from decimal import Decimal
from typing import Dict

from django.conf import settings
from prices import Money

from ... import TransactionKind
from ...models import Payment
from ...utils import create_transaction


def dummy_success():
    return True


def get_client_token(**connection_params):
    return str(uuid.uuid4())


def authorize(payment: Payment, payment_token: str, **connection_params):
    success = dummy_success()
    error = None
    if not success:
        error = 'Unable to authorize transaction'
    txn = create_transaction(
        payment=payment,
        kind=TransactionKind.AUTH,
        amount=payment.total,
        currency=payment.currency,
        gateway_response={},
        token=payment_token,
        is_success=success)
    return txn, error


def void(payment: Payment, **connection_params: Dict):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to void transaction'
    txn = create_transaction(
        payment=payment,
        kind=TransactionKind.VOID,
        amount=payment.total,
        currency=payment.currency,
        gateway_response={},
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def capture(payment: Payment, amount: Decimal):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process capture'
    txn = create_transaction(
        payment=payment,
        kind=TransactionKind.CAPTURE,
        amount=amount,
        currency=payment.currency,
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def refund(payment: Payment, amount: Decimal):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process refund'
    txn = create_transaction(
        payment=payment,
        kind=TransactionKind.REFUND,
        amount=amount,
        currency=payment.currency,
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error
