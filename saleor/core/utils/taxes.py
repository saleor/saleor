from django.conf import settings
from django.contrib.sites.models import Site
from django_countries.fields import Country
from django_prices_vatlayer.utils import (
    get_tax_for_rate, get_tax_rates_for_country)
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

DEFAULT_TAX_RATE_NAME = 'standard'

ZERO_MONEY = Money(0, settings.DEFAULT_CURRENCY)
ZERO_TAXED_MONEY = TaxedMoney(net=ZERO_MONEY, gross=ZERO_MONEY)


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

    keep_gross = include_taxes_in_prices()
    return tax_to_apply(base, keep_gross=keep_gross)


def get_taxes_for_country(country):
    tax_rates = get_tax_rates_for_country(country.code)
    if tax_rates is None:
        return None

    taxes = {DEFAULT_TAX_RATE_NAME: {
        'value': tax_rates['standard_rate'],
        'tax': get_tax_for_rate(tax_rates)}}
    if tax_rates['reduced_rates']:
        taxes.update({
            rate_name: {
                'value': tax_rates['reduced_rates'][rate_name],
                'tax': get_tax_for_rate(tax_rates, rate_name)}
            for rate_name in tax_rates['reduced_rates']})
    return taxes


def get_taxes_for_address(address):
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


def include_taxes_in_prices():
    return Site.objects.get_current().settings.include_taxes_in_prices


def display_gross_prices():
    return Site.objects.get_current().settings.display_gross_prices


def charge_taxes_on_shipping():
    return Site.objects.get_current().settings.charge_taxes_on_shipping
