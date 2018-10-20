import uuid

from ... import TransactionType
from ...utils import create_transaction


def dummy_success():
    return True


def get_client_token(**client_kwargs):
    return str(uuid.uuid4())


def authorize(payment, transaction_token, **client_kwargs):
    success = dummy_success()
    error = None
    if not success:
        error = 'Unable to authorize transaction'
    txn = create_transaction(
        payment=payment,
        transaction_type=TransactionType.AUTH,
        amount=payment.total,
        gateway_response={},
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def void(payment, **client_kwargs):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to void transaction'
    txn = create_transaction(
        payment=payment,
        transaction_type=TransactionType.VOID,
        amount=payment.total,
        gateway_response={},
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def capture(payment, amount=None):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process capture'
    txn = create_transaction(
        payment=payment,
        transaction_type=TransactionType.CAPTURE,
        amount=amount,
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def refund(payment, amount=None):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process refund'
    txn = create_transaction(
        payment=payment,
        transaction_type=TransactionType.REFUND,
        amount=amount,
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error
