from decimal import Decimal
from functools import wraps
from typing import Dict, Optional

from django.db import transaction

from . import PaymentError, PaymentMethodCaptureStatus, get_provider
from .models import PaymentMethod, Transaction


def validate_payment_method(view):
    """Decorate a view to check if payment method is active, so any actions
    can be performed on it.
    """
    @wraps(view)
    def func(payment_method, *args, **kwargs):
        if not payment_method.is_active:
            raise PaymentError('This payment method is no longer active.')
        return view(payment_method, *args, **kwargs)
    return func


def create_payment_method(**payment_data):
    payment_method, _ = PaymentMethod.objects.get_or_create(**payment_data)
    return payment_method


def create_transaction(
        payment_method: PaymentMethod, token: str, transaction_type: str,
        is_success: bool, amount: Decimal,
        gateway_response: Optional[Dict] = None) -> Transaction:
    if not gateway_response:
        gateway_response = {}

    txn, _ = Transaction.objects.get_or_create(
        payment_method=payment_method, token=token,
        transaction_type=transaction_type, is_success=is_success,
        amount=amount, gateway_response=gateway_response)
    return txn


def gateway_get_client_token(provider_name):
    provider, provider_params = get_provider(provider_name)
    return provider.get_client_token(**provider_params)


@validate_payment_method
def gateway_authorize(payment_method, transaction_token) -> Transaction:
    if not payment_method.charge_status == PaymentMethodCaptureStatus.NOT_CHARGED:
        raise PaymentError('Charged transactions cannot be authorized again.')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.authorize(
            payment_method, transaction_token, **provider_params)
        if txn.is_success:
            payment_method.charge_status = PaymentMethodCaptureStatus.NOT_CHARGED
            payment_method.save(update_fields=['charge_status'])
    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError(error)
    return txn


@validate_payment_method
def gateway_capture(payment_method, amount) -> Transaction:
    if payment_method.charge_status not in {
            PaymentMethodCaptureStatus.CHARGED,
            PaymentMethodCaptureStatus.NOT_CHARGED}:
        raise PaymentError('This payment method cannot be captured.')
    if amount > payment_method.total or amount > (
            payment_method.total - payment_method.captured_amount):
        raise PaymentError('Unable to capture more than authorized amount.')
    if amount <= 0:
        raise PaymentError('Amount should be a positive number.')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.capture(
            payment_method, amount=amount, **provider_params)
        if txn.is_success:
            payment_method.charge_status = PaymentMethodCaptureStatus.CHARGED
            payment_method.captured_amount += txn.amount
            payment_method.save(
                update_fields=['charge_status', 'captured_amount'])

    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError(error)
    return txn


@validate_payment_method
def gateway_void(payment_method) -> Transaction:
    if not payment_method.charge_status == PaymentMethodCaptureStatus.NOT_CHARGED:
        raise PaymentError('Only pre-authorized transactions can be void.')
    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.void(payment_method, **provider_params)
        if txn.is_success:
            payment_method.is_active = False
            payment_method.save(update_fields=['is_active'])
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment_method
def gateway_refund(payment_method, amount) -> Transaction:
    if amount > payment_method.captured_amount:
        raise PaymentError('Cannot refund more than captured')
    if amount <= 0:
        raise PaymentError('Amount should be a positive number.')
    if not payment_method.charge_status == PaymentMethodCaptureStatus.CHARGED:
        raise PaymentError(
            'Refund is possible only when transaction is captured.')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.refund(payment_method, amount, **provider_params)
        if txn.is_success:
            changed_fields = ['captured_amount']
            if txn.amount == payment_method.total:
                payment_method.charge_status = PaymentMethodCaptureStatus.FULLY_REFUNDED
                payment_method.is_active = False
                changed_fields += ['charge_status', 'is_active']
            payment_method.captured_amount -= amount
            payment_method.save(update_fields=changed_fields)
    if not txn.is_success:
        raise PaymentError(error)
    return txn
