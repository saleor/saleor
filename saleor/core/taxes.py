from dataclasses import dataclass
from typing import Union

from django.contrib.sites.models import Site
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange


class TaxError(Exception):
    """Default tax error."""


def zero_money(currency: str) -> Money:
    """Return a money object set to zero.

    This is a function used as a model's default.
    """
    return Money(0, currency)


def zero_taxed_money(currency: str) -> TaxedMoney:
    zero = zero_money(currency)
    return TaxedMoney(net=zero, gross=zero)


def include_taxes_in_prices() -> bool:
    return Site.objects.get_current().settings.include_taxes_in_prices


def display_gross_prices() -> bool:
    return Site.objects.get_current().settings.display_gross_prices


def charge_taxes_on_shipping() -> bool:
    return Site.objects.get_current().settings.charge_taxes_on_shipping


def get_display_price(
    base: Union[TaxedMoney, TaxedMoneyRange], display_gross: bool = False
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


@dataclass(frozen=True)
class TaxType:
    """Dataclass for unifying tax type object that comes from tax gateway."""

    code: str
    description: str
