import uuid
from django.db import transaction

from ... import TransactionType, PaymentMethodChargeStatus
from ...models import Transaction


def dummy_success():
    return True


def authorize(payment_method):
    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.AUTH,
        amount=payment_method.total,
        gateway_response={},
        defaults={
            'token': str(uuid.uuid4()),
            'is_success': dummy_success()})[0]
    return txn


def void(payment_method):
    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.VOID,
        amount=payment_method.total,
        gateway_response={},
        defaults={
            'token': str(uuid.uuid4()),
            'is_success': dummy_success()})[0]
    return txn


def charge(payment_method, amount=None):
    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.CHARGE,
        amount=amount,
        defaults={
            'token': str(uuid.uuid4()),
            'gateway_response': {},
            'is_success': dummy_success()})[0]
    return txn


def refund(payment_method, amount=None):
    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.REFUND,
        amount=amount,
        defaults={
            'token': str(uuid.uuid4()),
            'gateway_response': {},
            'is_success': dummy_success()})[0]
    return txn
