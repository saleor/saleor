from dataclasses import dataclass
from typing import Union

from django.conf import settings
from django.contrib.sites.models import Site
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

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


def get_display_price(
    base: Union[TaxedMoney, TaxedMoneyRange], display_gross=None
) -> Money:
    """Return price amount that should be displayed based on settings"""
    if not display_gross:
        display_gross = display_gross_prices()
    if isinstance(base, TaxedMoneyRange):
        if display_gross:
            base = MoneyRange(start=base.start.gross, stop=base.stop.gross)
        else:
            base = MoneyRange(start=base.start.net, stop=base.stop.net)

    if isinstance(base, TaxedMoney):
        base = base.gross if display_gross else base.net
    return base


@dataclass
class TaxType:
    """Dataclass for unifying tax type object that comes from tax gateway"""

    code: str
    description: str
