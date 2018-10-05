import importlib
from enum import Enum
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.translation import pgettext_lazy


class PaymentError(Exception):
    pass


class TransactionType:
    """
    - Authorization: An amount reserved against the customer's funding
                     source. Money does not change hands until the
                     authorization is captured.
    - Charge: Authorization and capture in a single step.
    - Void: A cancellation of a pending authorization.
    - Capture: A transfer of the money that was reserved during the
               authorization stage.
    - Refund: Full or partial return of captured funds to the customer.
    - Release: Release of the funds that were reserved during the authorization
               stage to the customer's funding source.
    """
    AUTH = 'auth'
    CHARGE = 'capture'
    CAPTURE = 'capture'
    VOID = 'void'
    REFUND = 'refund'
    RELEASE = 'release'

    CHOICES = [(AUTH, pgettext_lazy('transaction type', 'Authorization')),
               (CHARGE, pgettext_lazy('transaction type', 'Charge')),
               (REFUND, pgettext_lazy('transaction type', 'Refund')),
               (RELEASE, pgettext_lazy('transaction type', 'Release')),
               (CAPTURE, pgettext_lazy('transaction type', 'Capture')),
               (VOID, pgettext_lazy('transaction type', 'Void'))]


class PaymentMethodCaptureStatus:
    """
    - Charged: Funds were taken off the customer founding source, partly or
               completly covering the payment amount.
    - Not charged: No funds were take off the customer founding source yet.
    - Fully refunded: All charged funds were returned to the customer.
    """
    CHARGED = 'charged'
    NOT_CHARGED = 'not-charged'
    FULLY_REFUNDED = 'fully-refunded'

    CHOICES = [
        (CHARGED, pgettext_lazy('payment method status', 'Charged')),
        (NOT_CHARGED, pgettext_lazy('payment method status', 'Not charged')),
        (
            FULLY_REFUNDED,
            pgettext_lazy('payment method status', 'Fully refunded'))]


PROVIDERS_ENUM = Enum(
    'ProvidersEnum',
    {key.upper(): key.lower()
     for key in settings.PAYMENT_PROVIDERS})


def get_provider(provider_name):
    if provider_name not in settings.PAYMENT_PROVIDERS:
        raise ImproperlyConfigured(
            'Payment provider %s is not configured.' % provider_name)
    provider_module = importlib.import_module(
        settings.PAYMENT_PROVIDERS[provider_name]['module'])
    provider_params = settings.PAYMENT_PROVIDERS[provider_name][
        'connection_params']
    return provider_module, provider_params
