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
from .models import Payment, Transaction

logger = logging.getLogger(__name__)


def get_billing_data(order):
    data = {}
    if order.billing_address:
        data = {
            'billing_first_name': order.billing_address.first_name,
            'billing_last_name': order.billing_address.last_name,
            'billing_company_name': order.billing_address.company_name,
            'billing_address_1': order.billing_address.street_address_1,
            'billing_address_2': order.billing_address.street_address_2,
            'billing_city': order.billing_address.city,
            'billing_postal_code': order.billing_address.postal_code,
            'billing_country_code': order.billing_address.country.code,
            'billing_email': order.user_email,
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


def validate_payment(view):
    """Decorate a view to check if payment is authorized, so any actions
    can be performed on it.
    """

    @wraps(view)
    def func(payment: Payment, *args, **kwargs):
        if not payment.is_active:
            raise PaymentError('This payment is no longer active.')
        return view(payment, *args, **kwargs)
    return func


def create_payment(**payment_data):
    payment, _ = Payment.objects.get_or_create(**payment_data)
    return payment


def create_transaction(
        payment: Payment,
        token: str,
        transaction_type: str,
        is_success: bool,
        amount: Decimal,
        currency: str,
        gateway_response: Optional[Dict] = None) -> Transaction:
    if not gateway_response:
        gateway_response = {}
    txn, _ = Transaction.objects.get_or_create(
        payment=payment,
        token=token,
        transaction_type=transaction_type,
        is_success=is_success,
        amount=amount,
        currency=currency,
        gateway_response=gateway_response)
    return txn


def gateway_get_transaction_token(provider_name: str):
    # FIXME Add tests
    provider, provider_params = get_provider(provider_name)
    return provider.get_transaction_token(**provider_params)


@validate_payment
def gateway_authorize(payment: Payment, transaction_token: str) -> Transaction:
    if not payment.charge_status == ChargeStatus.NOT_CHARGED:
        raise PaymentError('Charged transactions cannot be authorized again.')

    provider, provider_params = get_provider(payment.variant)
    with transaction.atomic():
        txn, error = provider.authorize(
            payment, transaction_token, **provider_params)
            # FIXME Create an order event ?
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment
def gateway_capture(payment: Payment, amount: Decimal) -> Transaction:
    if amount <= 0:
        raise PaymentError('Amount should be a positive number.')
    if payment.charge_status not in {ChargeStatus.CHARGED,
                                     ChargeStatus.NOT_CHARGED}:
        raise PaymentError('This payment cannot be captured.')
    if amount > payment.total or amount > (
            payment.total - payment.captured_amount):
        raise PaymentError('Unable to capture more than authorized amount.')

    provider, provider_params = get_provider(payment.variant)
    with transaction.atomic():
        txn, error = provider.capture(
            payment, amount=amount, **provider_params)
        if txn.is_success:
            payment.charge_status = ChargeStatus.CHARGED
            payment.captured_amount += txn.amount
            payment.save(update_fields=['charge_status', 'captured_amount'])
            order = payment.order
            if order and order.is_fully_paid():
                handle_fully_paid_order(order)
            # FIXME Create an order event ?
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment
def gateway_void(payment) -> Transaction:
    if not can_be_voided(payment):
        raise PaymentError('Only pre-authorized transactions can be voided.')
    provider, provider_params = get_provider(payment.variant)
    with transaction.atomic():
        txn, error = provider.void(payment, **provider_params)
        if txn.is_success:
            payment.is_active = False
            payment.save(update_fields=['is_active'])
            # FIXME Create an order event ?
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment
def gateway_refund(payment, amount: Decimal) -> Transaction:
    if amount <= 0:
        raise PaymentError('Amount should be a positive number.')
    if amount > payment.captured_amount:
        raise PaymentError('Cannot refund more than captured')
    if not payment.charge_status == ChargeStatus.CHARGED:
        raise PaymentError(
            'Refund is possible only when transaction is captured.')

    provider, provider_params = get_provider(payment.variant)
    with transaction.atomic():
        txn, error = provider.refund(payment, amount, **provider_params)
        if txn.is_success:
            changed_fields = ['captured_amount']
            if txn.amount == payment.total:
                payment.charge_status = ChargeStatus.FULLY_REFUNDED
                payment.is_active = False
                changed_fields += ['charge_status', 'is_active']
            payment.captured_amount -= txn.amount
            payment.save(update_fields=changed_fields)
        # FIXME Create an order event ?
    if not txn.is_success:
        raise PaymentError(error)
    return txn
