from decimal import Decimal
from typing import Dict, Optional

from django.db import transaction

from . import PaymentError, PaymentMethodChargeStatus, get_provider
from .models import PaymentMethod, Transaction


def create_payment_method(**payment_method_kwargs):
    payment_method, dummy_created = PaymentMethod.objects.get_or_create(
        **payment_method_kwargs)
    return payment_method


def create_transaction(
        payment_method: PaymentMethod, token: str, transaction_type: str,
        is_success: bool, amount: Decimal,
        gateway_response: Optional[Dict] = None) -> Transaction:

    if not gateway_response:
        gateway_response = {}

    txn, dummy_created = Transaction.objects.get_or_create(
        payment_method=payment_method, token=token,
        transaction_type=transaction_type, is_success=is_success,
        amount=amount, gateway_response=gateway_response)
    return txn


def gateway_get_client_token(provider_name):
    provider, provider_params = get_provider(provider_name)
    return provider.get_client_token(**provider_params)


def gateway_authorize(payment_method, transaction_token) -> Transaction:
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if not payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED:
        raise PaymentError('Charged transactions cannot be authorized again')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.authorize(
            payment_method, transaction_token, **provider_params)
        if txn.is_success:
            payment_method.charge_status = PaymentMethodChargeStatus.NOT_CHARGED
            payment_method.save(update_fields=['charge_status'])
    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError(error)
    return txn


def gateway_charge(payment_method, amount) -> Transaction:
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if payment_method.charge_status not in {
            PaymentMethodChargeStatus.CHARGED,
            PaymentMethodChargeStatus.NOT_CHARGED}:
        raise PaymentError('This payment method cannot be charged')
    if amount > payment_method.total or amount > (
            payment_method.total - payment_method.captured_amount):
        raise PaymentError('Unable to charge more than authorized amount')
    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.charge(
            payment_method, amount=amount, **provider_params)
        if txn.is_success:
            payment_method.charge_status = PaymentMethodChargeStatus.CHARGED
            payment_method.captured_amount += txn.amount
            payment_method.save(
                update_fields=['charge_status', 'captured_amount'])

    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError(error)
    return txn


def gateway_void(payment_method) -> Transaction:
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if not payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED:
        raise PaymentError('Only pre-authorized transactions can be void')
    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.void(payment_method, **provider_params)
        if txn.is_success:
            payment_method.is_active = False
            payment_method.save(update_fields=['is_active'])
    if not txn.is_success:
        raise PaymentError(error)
    return txn


def gateway_refund(payment_method, amount) -> Transaction:
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if amount > payment_method.captured_amount:
        raise PaymentError('Cannot refund more than captured')
    if not payment_method.charge_status == PaymentMethodChargeStatus.CHARGED:
        raise PaymentError(
            'Refund is possible only when transaction is charged')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.refund(payment_method, amount, **provider_params)
        if txn.is_success:
            changed_fields = ['captured_amount']
            if txn.amount == payment_method.total:
                payment_method.charge_status = PaymentMethodChargeStatus.FULLY_REFUNDED
                payment_method.is_active = False
                changed_fields += ['charge_status', 'is_active']
            payment_method.captured_amount -= amount
            payment_method.save(update_fields=changed_fields)
    if not txn.is_success:
        raise PaymentError(error)
    return txn
