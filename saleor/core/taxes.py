from dataclasses import dataclass

from django.contrib.sites.models import Site
from prices import Money, TaxedMoney


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


def charge_taxes_on_shipping() -> bool:
    return Site.objects.get_current().settings.charge_taxes_on_shipping


@dataclass(frozen=True)
class TaxType:
    """Dataclass for unifying tax type object that comes from tax gateway."""

    code: str
    description: str
