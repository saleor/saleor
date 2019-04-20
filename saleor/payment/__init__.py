import importlib
from enum import Enum

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import pgettext_lazy


class PaymentError(Exception):

    def __init__(self, message):
        super(PaymentError, self).__init__(message)
        self.message = message


class GatewayError(IOError):
    pass


class CustomPaymentChoices:
    MANUAL = 'manual'

    CHOICES = [
        (MANUAL, pgettext_lazy('Custom payment choice type', 'Manual'))]


class OperationType(Enum):
    PROCESS_PAYMENT = 'process_payment'
    AUTH = 'authorize'
    CAPTURE = 'capture'
    CHARGE = 'charge'
    VOID = 'void'
    REFUND = 'refund'


class TransactionError(Enum):
    """Represents a transaction error."""

    INCORRECT_NUMBER = 'incorrect_number'
    INVALID_NUMBER = 'invalid_number'
    INCORRECT_CVV = 'incorrect_cvv'
    INVALID_CVV = 'invalid_cvv'
    INCORRECT_ZIP = 'incorrect_zip'
    INCORRECT_ADDRESS = 'incorrect_address'
    INVALID_EXPIRY_DATE = 'invalid_expiry_date'
    EXPIRED = 'expired'
    PROCESSING_ERROR = 'processing_error'
    DECLINED = 'declined'


class TransactionKind:
    """Represents the type of a transaction.

    The following transactions types are possible:
    - AUTH - an amount reserved against the customer's funding source. Money
    does not change hands until the authorization is captured.
    - CHARGE - authorization and capture in a single step.
    - VOID - a cancellation of a pending authorization or capture.
    - CAPTURE - a transfer of the money that was reserved during the
    authorization stage.
    - REFUND - full or partial return of captured funds to the customer.
    """

    AUTH = 'auth'
    CHARGE = 'charge'
    CAPTURE = 'capture'
    VOID = 'void'
    REFUND = 'refund'
    # FIXME we could use another status like WAITING_FOR_AUTH for transactions
    # Which were authorized, but needs to be confirmed manually by staff
    # eg. Braintree with "submit_for_settlement" enabled
    CHOICES = [(AUTH, pgettext_lazy('transaction kind', 'Authorization')),
               (CHARGE, pgettext_lazy('transaction kind', 'Charge')),
               (REFUND, pgettext_lazy('transaction kind', 'Refund')),
               (CAPTURE, pgettext_lazy('transaction kind', 'Capture')),
               (VOID, pgettext_lazy('transaction kind', 'Void'))]


class ChargeStatus:
    """Represents possible statuses of a payment.

    The following statuses are possible:
    - NOT_CHARGED - no funds were take off the customer founding source yet.
    - PARTIALLY_CHARGED - funds were taken off the customer's funding source,
    partly covering the payment amount.
    - FULLY_CHARGED - funds were taken off the customer founding source,
    partly or completely covering the payment amount.
    - PARTIALLY_REFUNDED - part of charged funds were returned to the customer.
    - FULLY_REFUNDED - all charged funds were returned to the customer.
    """

    NOT_CHARGED = 'not-charged'
    PARTIALLY_CHARGED = 'partially-charged'
    FULLY_CHARGED = 'fully-charged'
    PARTIALLY_REFUNDED = 'partially-refunded'
    FULLY_REFUNDED = 'fully-refunded'

    CHOICES = [
        (NOT_CHARGED, pgettext_lazy('payment status', 'Not charged')),
        (PARTIALLY_CHARGED, pgettext_lazy(
            'payment status', 'Partially charged')),
        (FULLY_CHARGED, pgettext_lazy('payment status', 'Fully charged')),
        (PARTIALLY_REFUNDED, pgettext_lazy(
            'payment status', 'Partially refunded')),
        (FULLY_REFUNDED, pgettext_lazy('payment status', 'Fully refunded'))]


GATEWAYS_ENUM = Enum(
    'GatewaysEnum',
    {key.upper(): key.lower()
     for key in settings.CHECKOUT_PAYMENT_GATEWAYS})


def get_payment_gateway(gateway_name):
    if gateway_name not in settings.CHECKOUT_PAYMENT_GATEWAYS:
        raise ValueError('%s is not allowed gateway' % gateway_name)
    if gateway_name not in settings.PAYMENT_GATEWAYS:
        raise ImproperlyConfigured(
            'Payment gateway %s is not configured.' % gateway_name)
    gateway_module = importlib.import_module(
        settings.PAYMENT_GATEWAYS[gateway_name]['module'])
    gateway_params = settings.PAYMENT_GATEWAYS[gateway_name][
        'connection_params']
    return gateway_module, gateway_params
