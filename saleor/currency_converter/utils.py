from __future__ import unicode_literals

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from prices import Price

from .models import Rate, RateSource


class CurrencyConversionException(Exception):
    """
    Raised by conversion utility function when problems arise
    """


def get_default_backend():
    """
    Return default currency converter backend instance
    """

    try:
        default_backend = settings.CURRENCY_CONVERTER['DEFAULT_BACKEND']
    except AttributeError:
        raise ImproperlyConfigured(
            'Currency converter backend is not configured'
        )

    path = default_backend.split('.')

    module_path = '.'.join(path[:-1])
    klass_name = path[-1]
    module = __import__(module_path, globals(), locals(), [klass_name])
    klass = getattr(module, klass_name)

    return klass()


def get_rate(currency):
    """Returns the rate from the default currency to `currency`."""
    source = get_rate_source()

    try:
        if not Rate.objects.today_rates().exists():
            # Refresh rates
            source.update_rates()
        return Rate.objects.today_rates().get(
            source=source, currency=currency
        ).value
    except Rate.DoesNotExist:
        raise CurrencyConversionException(
            "Rate for %s in %s do not exists. " % (currency, source.name))


def get_rate_source():
    """Get the default Rate Source and return it."""
    backend = get_default_backend()
    try:
        source = RateSource.objects.filter(name=backend.get_source_name())
        if not source.exists():
            backend.update_rates()
            # We have to hit DB again (RateSource was created now)
        return RateSource.objects.get(name=backend.get_source_name())
    except RateSource.DoesNotExist:
        raise CurrencyConversionException(
            "Rate for %s source do not exists. " % backend.get_source_name()
        )


def base_convert_money(amount, currency_from, currency_to):
    """
    Convert 'amount' from 'currency_from' to 'currency_to'
    """
    source = get_rate_source()

    # Get rate for currency_from.
    if source.base_currency != currency_from:
        rate_from = get_rate(currency_from)
    else:
        # If currency from is the same as base currency its rate is 1.
        rate_from = Decimal(1)

    # Get rate for currency_to.
    rate_to = get_rate(currency_to)

    # After finishing the operation, quantize down final amount to two points.
    return ((amount / rate_from) * rate_to).quantize(Decimal("1.00"))


def convert_price(price, currency_to):
    """
    Convert 'price' (Price object) from it's currency to 'currency_to' a
    d return new Price instance.
    """
    new_amount = base_convert_money(price.gross, price.currency, currency_to)

    return Price(new_amount, currency=currency_to)