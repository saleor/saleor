import importlib
from enum import Enum
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.translation import pgettext_lazy


class PaymentError(Exception):
    pass


class TransactionType:
    AUTH = 'auth'
    CHARGE = 'charge'
    VOID = 'void'
    REFUND = 'refund'

    CHOICES = [(AUTH, pgettext_lazy('transaction type', 'Authorization')),
               (CHARGE, pgettext_lazy('transaction type', 'Charge')),
               (REFUND, pgettext_lazy('transaction type', 'Refund')),
               (VOID, pgettext_lazy('transaction type', 'Void'))]


class PaymentMethodChargeStatus:
    CHARGED = 'charged'
    NOT_CHARGED = 'not-charged'
    FULLY_REFUNDED = 'fully-refunded'

    CHOICES = [
        (CHARGED, pgettext_lazy('payment method status', 'Charged')),
        (NOT_CHARGED, pgettext_lazy('payment method status', 'Not charged')), (
            FULLY_REFUNDED,
            pgettext_lazy('payment method status', 'Fully refunded'))]


PROVIDERS_ENUM = Enum(
    'ProvidersEnum',
    {key.upper(): key.lower() for key in settings.PAYMENT_PROVIDERS})

def get_provider(provider_name):
    if provider_name not in settings.PAYMENT_PROVIDERS:
        raise ImproperlyConfigured(
            f'Payment provider {provider_name} is not configured.')
    provider_module = importlib.import_module(
        settings.PAYMENT_PROVIDERS[provider_name]['module'])
    provider_params = settings.PAYMENT_PROVIDERS[provider_name]['connection_params']
    return provider_module, provider_params
