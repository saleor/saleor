from dataclasses import dataclass
from typing import List

from prices import Money, TaxedMoney

from ..core.schema import DecimalType, WebhookResponseBase


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


@dataclass(frozen=True)
class TaxType:
    """Dataclass for unifying tax type object that comes from tax gateway."""

    code: str
    description: str


class TaxLineData(WebhookResponseBase):
    tax_rate: DecimalType
    total_gross_amount: DecimalType
    total_net_amount: DecimalType


class TaxData(WebhookResponseBase):
    shipping_price_gross_amount: DecimalType
    shipping_price_net_amount: DecimalType
    shipping_tax_rate: DecimalType
    lines: List[TaxLineData]
