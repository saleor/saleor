from dataclasses import dataclass
from decimal import Decimal
from typing import Union

from babel.numbers import get_currency_precision
from django.conf import settings
from django.contrib.sites.models import Site
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange


class TaxError(Exception):
    """Default tax error."""


def zero_money(currency=None):
    """Return a money object set to zero.

    This is a function used as a model's default.
    """

    if currency is None:
        currency = settings.DEFAULT_CURRENCY
    return Money(0, currency)


def zero_taxed_money(currency=settings.DEFAULT_CURRENCY):
    zero = zero_money(currency)
    return TaxedMoney(net=zero, gross=zero)


def include_taxes_in_prices():
    return Site.objects.get_current().settings.include_taxes_in_prices


def display_gross_prices():
    return Site.objects.get_current().settings.display_gross_prices


def charge_taxes_on_shipping():
    return Site.objects.get_current().settings.charge_taxes_on_shipping


def get_display_price(
    base: Union[TaxedMoney, TaxedMoneyRange], display_gross=None
) -> Money:
    """Return the price amount that should be displayed based on settings."""
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


def quantize_price(
    price: Union["TaxedMoney", "Money", "Decimal", "TaxedMoneyRange"], currency
):
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return price.quantize(number_places)


@dataclass(frozen=True)
class TaxType:
    """Dataclass for unifying tax type object that comes from tax gateway."""

    code: str
    description: str
