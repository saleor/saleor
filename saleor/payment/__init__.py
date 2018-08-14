from django.utils.translation import pgettext_lazy
import importlib
from django.core.exceptions import ImproperlyConfigured


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


# FIXME: move to settings
PROVIDERS_MAP = {'dummy': 'saleor.payment.providers.dummy'}


def get_provider(provider_name):
    if provider_name not in PROVIDERS_MAP:
        raise ImproperlyConfigured(
            f'Payment provider {provider_name} is not configured.')
    provider_module = importlib.import_module(PROVIDERS_MAP[provider_name])

    return provider_module
