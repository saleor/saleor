from django.db import transaction

from . import PaymentError, PaymentMethodChargeStatus, get_provider


def gateway_authorize(payment_method):
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if not payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED:
        raise PaymentError('Charged transactions cannot be authorized again')

    provider = get_provider(payment_method.variant)
    with transaction.atomic():
        txn = provider.authorize(payment_method)
        if txn.is_success:
            payment_method.charge_status = PaymentMethodChargeStatus.NOT_CHARGED
            payment_method.save(update_fields=['charge_status'])
    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError('Unable to authorize transaction')
    return txn


def gateway_charge(payment_method, amount):
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if not payment_method.charge_status in {
            PaymentMethodChargeStatus.CHARGED,
            PaymentMethodChargeStatus.NOT_CHARGED}:
        raise PaymentError('This payment method cannot be charged')
    if amount > payment_method.total or amount > (
            payment_method.total - payment_method.captured_amount):
        raise PaymentError('Unable to charge more than authozied amount')
    provider = get_provider(payment_method.variant)
    with transaction.atomic():
        txn = provider.charge(payment_method, amount=amount)
        if txn.is_success:
            payment_method.charge_status = PaymentMethodChargeStatus.CHARGED
            payment_method.captured_amount += txn.amount
            payment_method.save(
                update_fields=['charge_status', 'captured_amount'])

    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError('Unable to process transaction')
    return txn


def gateway_void(payment_method):
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if not payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED:
        raise PaymentError('Only pre-authorized transactions can be void')
    provider = get_provider(payment_method.variant)
    with transaction.atomic():
        txn = provider.void(payment_method)
        if txn.is_success:
            payment_method.is_active = False
            payment_method.save(update_fields=['is_active'])
    if not txn.is_success:
        raise PaymentError('Unable to void transaction')
    return txn


def gateway_refund(payment_method, amount):
    if not payment_method.is_active:
        raise PaymentError('This payment method is no longer active')
    if amount > payment_method.captured_amount:
        raise PaymentError('Cannot refund more than captured')
    if not payment_method.charge_status == PaymentMethodChargeStatus.CHARGED:
        raise PaymentError(
            'Refund is possible only when transaction is charged')

    provider = get_provider(payment_method.variant)
    with transaction.atomic():
        txn = provider.refund(payment_method, amount)
        if txn.is_success:
            changed_fields = ['captured_amount']
            if txn.amount == payment_method.total:
                payment_method.charge_status = PaymentMethodChargeStatus.FULLY_REFUNDED
                payment_method.is_active = False
                changed_fields += ['charge_status', 'is_active']
            payment_method.captured_amount -= amount
            payment_method.save(update_fields=changed_fields)
    if not txn.is_success:
        raise PaymentError('Unable to process refund')
    return txn
