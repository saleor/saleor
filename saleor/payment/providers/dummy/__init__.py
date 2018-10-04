import uuid

from ... import TransactionType
from ...utils import create_transaction


def dummy_success():
    return True


def get_client_token(**client_kwargs):
    return str(uuid.uuid4())


def authorize(payment_method, transaction_token, **client_kwargs):
    success = dummy_success()
    error = None
    if not success:
        error = 'Unable to authorize transaction'
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.AUTH,
        amount=payment_method.total,
        gateway_response={},
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def void(payment_method, **client_kwargs):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to void transaction'
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.VOID,
        amount=payment_method.total,
        gateway_response={},
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def charge(payment_method, amount=None):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process charge'
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.CHARGE,
        amount=amount,
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error


def refund(payment_method, amount=None):
    error = None
    success = dummy_success()
    if not success:
        error = 'Unable to process refund'
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.REFUND,
        amount=amount,
        token=str(uuid.uuid4()),
        is_success=success)
    return txn, error
