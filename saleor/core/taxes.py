from dataclasses import dataclass
from decimal import Decimal

from prices import Money, TaxedMoney
from pydantic import Field

from ..core.json_schema import WebhookResponseBase


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
    tax_rate: Decimal = Field(
        description="Tax rate value provided as percentage. "
        "Example: provide 23 to represent the 23% tax rate."
    )
    total_gross_amount: Decimal = Field(description="Gross price of the line.")
    total_net_amount: Decimal = Field(description="Net price of the line.")


class TaxData(WebhookResponseBase):
    shipping_tax_rate: Decimal = Field(description="Tax rate of shipping.")
    shipping_price_gross_amount: Decimal = Field(
        description="The gross price of shipping."
    )
    shipping_price_net_amount: Decimal = Field(description="Net price of shipping.")
    lines: list[TaxLineData] = Field(
        description="List of lines tax assigned to checkout. Lines should be "
        "returned in the same order in which they were sent to the App."
    )
