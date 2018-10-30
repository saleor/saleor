import logging
from decimal import Decimal
from functools import wraps
from typing import Dict, Optional

from django.conf import settings
from django.db import transaction
from prices import Money

from . import ChargeStatus, PaymentError, get_payment_gateway
from ..core import analytics
from ..order import OrderEvents, OrderEventsEmails
from ..order.emails import send_payment_confirmation
from .models import Payment, Transaction

logger = logging.getLogger(__name__)


def get_billing_data(order):
    """Extracts order's billing address into payment-friendly billing data."""
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
        kind: str,
        is_success: bool,
        amount: Decimal,
        currency: str,
        gateway_response: Optional[Dict] = None) -> Transaction:
    if not gateway_response:
        gateway_response = {}
    txn, _ = Transaction.objects.get_or_create(
        payment=payment,
        token=token,
        kind=kind,
        is_success=is_success,
        amount=amount,
        currency=currency,
        gateway_response=gateway_response)
    return txn


def gateway_get_client_token(gateway_name: str):
    """Gets client token, that will be used as a customer's identificator for
    client-side tokenization of the chosen payment method.
    """
    gateway, gateway_params = get_payment_gateway(gateway_name)
    return gateway.get_client_token(**gateway_params)


def clean_capture(payment: Payment, amount: Decimal):
    """Checks if payment can be captured."""
    if amount <= 0:
        raise PaymentError('Amount should be a positive number.')
    if not payment.can_capture():
        raise PaymentError('This payment cannot be captured.')
    if amount > payment.total or amount > (
            payment.total - payment.captured_amount):
        raise PaymentError('Unable to capture more than authorized amount.')


def clean_authorize(payment: Payment):
    """Checks if payment can be authorized."""
    if not payment.can_authorize():
        raise PaymentError('Charged transactions cannot be authorized again.')


@validate_payment
def gateway_charge(
        payment: Payment,
        payment_token: str,
        amount: Decimal) -> Transaction:
    """Performs authorization and capture in a single run.

    For gateways not supporting the authorization it should be a
    dedicated CHARGE transaction.

    For gateways not supporting capturing without authorizing,
    it should create two transaction - auth and capture, but only the last one
    is returned.
    """
    clean_authorize(payment)
    clean_capture(payment, amount)

    gateway, gateway_params = get_payment_gateway(payment.gateway)
    with transaction.atomic():
        txn, error = gateway.charge(
            payment, payment_token, **gateway_params)
        if txn.is_success:
            payment.charge_status = ChargeStatus.CHARGED
            payment.captured_amount += txn.amount
            payment.save(update_fields=['charge_status', 'captured_amount'])
            order = payment.order
            if order and order.is_fully_paid():
                handle_fully_paid_order(order)
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment
def gateway_authorize(payment: Payment, payment_token: str) -> Transaction:
    """Authorizes the payment and creates relevant transaction.

    Args:
     - payment_token: One-time-use reference to payment information.
    """
    clean_authorize(payment)

    gateway, gateway_params = get_payment_gateway(payment.gateway)
    with transaction.atomic():
        txn, error = gateway.authorize(
            payment, payment_token, **gateway_params)
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment
def gateway_capture(payment: Payment, amount: Decimal) -> Transaction:
    """Captures the money that was reserved during the authorization stage."""
    clean_capture(payment, amount)

    gateway, gateway_params = get_payment_gateway(payment.gateway)
    with transaction.atomic():
        txn, error = gateway.capture(
            payment, amount=amount, **gateway_params)
        if txn.is_success:
            payment.charge_status = ChargeStatus.CHARGED
            payment.captured_amount += txn.amount
            payment.save(update_fields=['charge_status', 'captured_amount'])
            order = payment.order
            if order and order.is_fully_paid():
                handle_fully_paid_order(order)
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment
def gateway_void(payment) -> Transaction:
    if not payment.can_void():
        raise PaymentError('Only pre-authorized transactions can be voided.')
    gateway, gateway_params = get_payment_gateway(payment.gateway)
    with transaction.atomic():
        txn, error = gateway.void(payment, **gateway_params)
        if txn.is_success:
            payment.is_active = False
            payment.save(update_fields=['is_active'])
    if not txn.is_success:
        raise PaymentError(error)
    return txn


@validate_payment
def gateway_refund(payment, amount: Decimal) -> Transaction:
    """Refunds the charged funds back to the customer.
    Refunds can be total or partial.
    """
    if amount <= 0:
        raise PaymentError('Amount should be a positive number.')
    if amount > payment.captured_amount:
        raise PaymentError('Cannot refund more than captured')
    if not payment.can_refund():
        raise PaymentError('This payment cannot be refunded.')

    gateway, gateway_params = get_payment_gateway(payment.gateway)
    with transaction.atomic():
        txn, error = gateway.refund(payment, amount, **gateway_params)
        if txn.is_success:
            changed_fields = ['captured_amount']
            payment.captured_amount -= txn.amount
            if not payment.captured_amount:
                payment.charge_status = ChargeStatus.FULLY_REFUNDED
                payment.is_active = False
                changed_fields += ['charge_status', 'is_active']
            payment.save(update_fields=changed_fields)
    if not txn.is_success:
        raise PaymentError(error)
    return txn
