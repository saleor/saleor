from django.conf import settings
from django.contrib.sites.models import Site
from prices import Money, TaxedMoney

ZERO_MONEY = Money(0, settings.DEFAULT_CURRENCY)

ZERO_TAXED_MONEY = TaxedMoney(net=ZERO_MONEY, gross=ZERO_MONEY)


def zero_money():
    """Function used as a model's default."""
    return ZERO_MONEY


def include_taxes_in_prices():
    return Site.objects.get_current().settings.include_taxes_in_prices


def display_gross_prices():
    return Site.objects.get_current().settings.display_gross_prices


def charge_taxes_on_shipping():
    return Site.objects.get_current().settings.charge_taxes_on_shipping
