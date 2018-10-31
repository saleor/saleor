from decimal import Decimal

import razorpay
import uuid
from typing import Dict, Tuple

from ... import TransactionKind
from ...utils import create_transaction
from ...models import Payment, Transaction

from .forms import RazorPaymentForm


E_ORDER_NOT_CHARGED = 'Order was not charged.'


def _generate_transaction(
        payment, kind: str, amount=None,
        *, id='', is_success=True, **data):

    if type(amount) is int:
        amount = Decimal(amount) / 100
    elif amount is None:
        amount = payment.total

    transaction = create_transaction(
        payment=payment,
        kind=kind,
        amount=amount,
        currency=data.pop('currency', payment.currency),
        gateway_response=data,
        token=id,
        is_success=is_success)

    return transaction


def get_form_class():
    return RazorPaymentForm


def get_client(public_key, secret_key, **_):
    razorpay_client = razorpay.Client(auth=(public_key, secret_key))
    return razorpay_client


def get_client_token(**_):
    return str(uuid.uuid4())


def charge(
        payment: Payment,
        payment_token: str,
        amount: Decimal,
        **connection_params: Dict) -> Tuple[Transaction, str]:

    int_amount = int(amount) * 100
    razorpay_client = get_client(**connection_params)
    response = razorpay_client.payment.capture(payment_token, int_amount)

    transaction = _generate_transaction(
        payment=payment, kind=TransactionKind.CHARGE, **response)
    return transaction, ''


def refund(payment, amount: Decimal, **connection_params):
    error = ''
    capture_txn = payment.transactions.filter(
        kind=TransactionKind.CHARGE, is_success=True).first()

    if capture_txn is not None:
        int_amount = int(amount * 100)
        razorpay_client = get_client(**connection_params)
        response = razorpay_client.payment.refund(
            capture_txn.token, int_amount)
    else:
        response = {'is_success': False}
        error = E_ORDER_NOT_CHARGED

    transaction = _generate_transaction(
        payment=payment, kind=TransactionKind.REFUND, **response)
    return transaction, error


def void(payment, **params):
    transaction = _generate_transaction(
        payment=payment, kind=TransactionKind.VOID,
        id=get_client_token(**params))
    return transaction, ''
