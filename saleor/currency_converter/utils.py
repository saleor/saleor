from __future__ import unicode_literals

from decimal import Decimal

from prices import Price

from .models import Rate, RateSource
from .backends import OpenExchangeBackend


class CurrencyConversionException(Exception):
    """
    Raised by conversion utility function when problems arise
    """



def get_rate(currency):
    """Returns the rate from the default currency to `currency`."""
    backend = OpenExchangeBackend()

    try:
        if not Rate.objects.today_rates().filter(
                source__name=backend.get_name()).exists():
            # Refresh rates
            backend.update_rates()
        return Rate.objects.today_rates().get(
            source__name=backend.get_name(), currency=currency
        ).value
    except Rate.DoesNotExist:
        raise CurrencyConversionException(
            "Rate for %s in %s do not exists. " % (currency,
                                                   backend.get_name()))



def base_convert_money(amount, currency_from, currency_to):
    """
    Convert 'amount' from 'currency_from' to 'currency_to'
    """
    source = OpenExchangeBackend()

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