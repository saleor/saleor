from dataclasses import dataclass
from decimal import Decimal

from prices import Money, TaxedMoney

TAX_ERROR_FIELD_LENGTH = 255


class TaxError(Exception):
    """Default tax error."""


class TaxDataError(Exception):
    """Error in tax data received from tax app or plugin."""

    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


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


@dataclass(frozen=True)
class TaxLineData:
    tax_rate: Decimal
    total_gross_amount: Decimal
    total_net_amount: Decimal


@dataclass(frozen=True)
class TaxData:
    shipping_price_gross_amount: Decimal
    shipping_price_net_amount: Decimal
    shipping_tax_rate: Decimal
    lines: list[TaxLineData]


class TaxDataErrorMessage:
    EMPTY = "Empty tax data."
    NEGATIVE_VALUE = "Tax data contains negative values."
    LINE_NUMBER = (
        "Number of lines from tax data doesn't match the line number from order."
    )
    OVERFLOW = "Tax data contains prices exceeding a billion or tax rate over 100%."
