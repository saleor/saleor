import uuid
from django.db import transaction

from ... import TransactionType, PaymentMethodChargeStatus
from ...utils import create_transaction

def dummy_success():
    return True


def authorize(payment_method, transaction_token):
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.AUTH,
        amount=payment_method.total,
        gateway_response={},
        token=str(uuid.uuid4()),
        is_success=dummy_success())
    return txn


def void(payment_method):
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.VOID,
        amount=payment_method.total,
        gateway_response={},
        token=str(uuid.uuid4()),
        is_success=dummy_success())
    return txn


def charge(payment_method, amount=None):
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.CHARGE,
        amount=amount,
        token=str(uuid.uuid4()),
        is_success=dummy_success())
    return txn


def refund(payment_method, amount=None):
    txn = create_transaction(
        payment_method=payment_method,
        transaction_type=TransactionType.REFUND,
        amount=amount,
        token=str(uuid.uuid4()),
        is_success=dummy_success())
    return txn
