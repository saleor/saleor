from django.conf import settings
from django.contrib.sites.models import Site
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

DEFAULT_TAX_RATE_NAME = 'standard'

ZERO_TAXED_MONEY = TaxedMoney(
    net=Money(0, settings.DEFAULT_CURRENCY),
    gross=Money(0, settings.DEFAULT_CURRENCY))


def apply_tax_to_price(taxes, rate_name, base):
    if not taxes or not rate_name:
        # Naively convert Money to TaxedMoney for consistency with price
        # handling logic across the codebase, passthrough other money types
        if isinstance(base, Money):
            return TaxedMoney(net=base, gross=base)
        if isinstance(base, MoneyRange):
            return TaxedMoneyRange(
                apply_tax_to_price(taxes, rate_name, base.start),
                apply_tax_to_price(taxes, rate_name, base.stop))
        if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
            return base
        raise TypeError('Unknown base for flat_tax: %r' % (base,))

    if rate_name in taxes:
        tax_to_apply = taxes[rate_name]['tax']
    else:
        tax_to_apply = taxes[DEFAULT_TAX_RATE_NAME]['tax']

    keep_gross = Site.objects.get_current().settings.include_taxes_in_prices
    return tax_to_apply(base, keep_gross=keep_gross)


def get_taxes_for_address(address):
    from . import get_taxes_for_country
    """Return proper taxes for address or default country."""
    if address is not None:
        country = address.country
    else:
        country = Country(settings.DEFAULT_COUNTRY)

    return get_taxes_for_country(country)


def get_tax_rate_by_name(rate_name, taxes=None):
    """Return value of tax rate for current taxes."""
    if not taxes or not rate_name:
        tax_rate = 0
    elif rate_name in taxes:
        tax_rate = taxes[rate_name]['value']
    else:
        tax_rate = taxes[DEFAULT_TAX_RATE_NAME]['value']

    return tax_rate
