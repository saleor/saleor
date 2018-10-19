import logging
from decimal import Decimal
from functools import wraps
from typing import Dict, Optional

from django.conf import settings
from django.db import transaction
from prices import Money

from . import ChargeStatus, PaymentError, can_be_voided, get_provider
from ..core import analytics
from ..order import OrderEvents, OrderEventsEmails
from ..order.emails import send_payment_confirmation
from .models import PaymentMethod, Transaction

logger = logging.getLogger(__name__)


def get_billing_data(order):
    data = {}
    if order.billing_address:
        data = {
            'billing_first_name': order.billing_address.first_name,
            'billing_last_name': order.billing_address.last_name,
            'billing_address_1': order.billing_address.street_address_1,
            'billing_address_2': order.billing_address.street_address_2,
            'billing_city': order.billing_address.city,
            'billing_postal_code': order.billing_address.postal_code,
            'billing_country_code': order.billing_address.country,
            'billing_country_area': order.billing_address.country_area}
    return data


def handle_fully_paid_order(order):
    order.events.create(type=OrderEvents.ORDER_FULLY_PAID.value)
    if order.get_user_current_email():
        send_payment_confirmation.delay(order.pk)
        order.events.create(
            type=OrderEvents.EMAIL_SENT.value,
            parameters={
                'email': order.get_user_current_email(),
                'email_type': OrderEventsEmails.PAYMENT.value})
    try:
        analytics.report_order(order.tracking_client_id, order)
    except Exception:
        # Analytics failing should not abort the checkout flow
        logger.exception('Recording order in analytics failed')


def validate_payment_method(view):
    """Decorate a view to check if payment method is active, so any actions
    can be performed on it.
    """
    @wraps(view)
    def func(payment_method: PaymentMethod, *args, **kwargs):
        if not payment_method.is_active:
            raise PaymentError('This payment method is no longer active.')
        return view(payment_method=payment_method, *args, **kwargs)
    return func


def validate_positive_amount(view):
    """Decorate a view to check if payment method is active, so any actions
    can be performed on it.
    """
    @wraps(view)
    def func(amount: Decimal, *args, **kwargs):
        if amount <= 0:
            raise PaymentError('Amount should be a positive number.')
        amount = Money(amount, currency=settings.DEFAULT_CURRENCY)
        return view(*args, amount=amount, **kwargs)
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


def gateway_get_client_token(provider_name: str):
    # FIXME Add tests

    provider, provider_params = get_provider(provider_name)
    return provider.get_client_token(**provider_params)


@validate_payment_method
def gateway_authorize(
        payment_method: PaymentMethod,
        transaction_token: str) -> Transaction:
    if not payment_method.charge_status == ChargeStatus.NOT_CHARGED:
        raise PaymentError('Charged transactions cannot be authorized again.')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.authorize(
            payment_method, transaction_token, **provider_params)
        if txn.is_success:
            payment_method.charge_status = ChargeStatus.NOT_CHARGED
            payment_method.save(update_fields=['charge_status'])
    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError(error)
    return txn


@validate_payment_method
@validate_positive_amount
def gateway_capture(
        payment_method: PaymentMethod,
        amount: Decimal) -> Transaction:
    if payment_method.charge_status not in {
            ChargeStatus.CHARGED,
            ChargeStatus.NOT_CHARGED}:
        raise PaymentError('This payment method cannot be captured.')
    if amount > payment_method.total.gross or amount > (
            payment_method.total.gross - payment_method.captured_amount):
        raise PaymentError('Unable to capture more than authorized amount.')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.capture(
            payment_method, amount=amount, **provider_params)
        if txn.is_success:
            payment_method.charge_status = ChargeStatus.CHARGED
            payment_method.captured_amount += txn.amount
            payment_method.save(
                update_fields=['charge_status', 'captured_amount'])
            order = payment_method.order
            if order and order.is_fully_paid():
                handle_fully_paid_order(order)
    if not txn.is_success:
        # TODO: Handle gateway response here somehow
        raise PaymentError(error)
    return txn


@validate_payment_method
def gateway_void(payment_method) -> Transaction:
    if not can_be_voided(payment_method):
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
@validate_positive_amount
def gateway_refund(
        payment_method,
        amount: Decimal) -> Transaction:
    if amount > payment_method.captured_amount:
        raise PaymentError('Cannot refund more than captured')
    if not payment_method.charge_status == ChargeStatus.CHARGED:
        raise PaymentError(
            'Refund is possible only when transaction is captured.')

    provider, provider_params = get_provider(payment_method.variant)
    with transaction.atomic():
        txn, error = provider.refund(payment_method, amount, **provider_params)
        if txn.is_success:
            changed_fields = ['captured_amount']
            if txn.amount == payment_method.total.gross:
                payment_method.charge_status = ChargeStatus.FULLY_REFUNDED
                payment_method.is_active = False
                changed_fields += ['charge_status', 'is_active']
            payment_method.captured_amount -= amount
            payment_method.save(update_fields=changed_fields)
    if not txn.is_success:
        raise PaymentError(error)
    return txn
