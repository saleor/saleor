from __future__ import unicode_literals
from decimal import Decimal
import operator

from prices import Price, PriceModifier, History

from .models import OpenExchangeRate
from .backends import OpenExchangeBackend


class CurrencyConversionException(Exception):
    """
    Raised by conversion utility function when problems arise
    """


class CurrencyConversion(PriceModifier):
    """
    Converts Price from one currency to another using PriceModifier
    """
    def __init__(self, target_currency):
        self.target_currency = target_currency
        self.rate_to = None

    def __repr__(self):
        return 'CurrencyConversion(to_currency=%s, exchange_rate=%r)' % (
            str(self.target_currency), self.rate_to)

    def apply(self, price):
        net_conversion = base_convert_money(price.net, price.currency,
                                            self.target_currency)
        net_amount = net_conversion['value']
        self.rate_to = net_conversion['rate_to']

        gross_amount = base_convert_money(price.gross, price.currency,
                                          self.target_currency)['value']

        history = History(price, operator.__mul__, self)

        return Price(net=net_amount, gross=gross_amount,
                     currency=self.target_currency, history=history)


def get_rate(currency):
    """Returns the rate from the default currency to `currency`."""
    backend = OpenExchangeBackend()

    try:
        if not OpenExchangeRate.objects.today_rates().exists():
            # Refresh rates
            backend.update_rates()
        return OpenExchangeRate.objects.today_rates().get(
            target_currency=currency
        ).exchange_rate
    except OpenExchangeRate.DoesNotExist:
        raise ValueError("Rate for %s in %s do not exists. " % (
            currency, backend.source_name))


def base_convert_money(amount, currency_from, currency_to):
    """
    Converts 'amount' from 'currency_from' to 'currency_to'
    """
    source = OpenExchangeBackend()

    # Get rate for currency_from.
    if source.get_base_currency() != currency_from:
        rate_from = get_rate(currency_from)
    else:
        # If currency from is the same as base currency its rate is 1.
        rate_from = Decimal(1)

    # Get rate for currency_to.
    rate_to = get_rate(currency_to)

    # After finishing the operation, quantize down final amount to two points.
    return {
        'value': ((amount / rate_from) * rate_to),
        'rate_from': rate_from,
        'rate_to': rate_to}


def convert_price(price, currency_to):
    """
    Convert 'price' (Price object) from it's currency to 'currency_to' a
    d return Price instance with applied CurrencyConversion modifier.
    """
    conversion = CurrencyConversion(target_currency=currency_to)

    return conversion.apply(price)

