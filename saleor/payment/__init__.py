import importlib
from enum import Enum
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.translation import pgettext_lazy


class PaymentError(Exception):

    def __init__(self, message):
        super(PaymentError, self).__init__(message)
        self.message = message


class CustomPaymentChoices:
    MANUAL = 'manual'

    CHOICES = [
        (MANUAL, pgettext_lazy('Custom payment choice type', 'Manual'))]


class TransactionError(Enum):
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
    """
    - Authorization: An amount reserved against the customer's funding
                     source. Money does not change hands until the
                     authorization is captured.
    - Charge: Authorization and capture in a single step.
    - Void: A cancellation of a pending authorization or capture.
    - Capture: A transfer of the money that was reserved during the
               authorization stage.
    - Refund: Full or partial return of captured funds to the customer.
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
    """
    - Charged: Funds were taken off the customer founding source, partly or
               completely covering the payment amount.
    - Not charged: No funds were take off the customer founding source yet.
    - Fully refunded: All charged funds were returned to the customer.
    """
    CHARGED = 'charged'
    NOT_CHARGED = 'not-charged'
    FULLY_REFUNDED = 'fully-refunded'
    # FIXME
    # We could probably support other statuses, like:
    # partially refunded
    # fully charged
    # ...?
    CHOICES = [
        (CHARGED, pgettext_lazy('payment status', 'Charged')),
        (NOT_CHARGED, pgettext_lazy('payment status', 'Not charged')),
        (FULLY_REFUNDED, pgettext_lazy('payment status', 'Fully refunded'))]


GATEWAYS_ENUM = Enum(
    'GatewaysEnum',
    {key.upper(): key.lower()
     for key in settings.PAYMENT_GATEWAYS})


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
