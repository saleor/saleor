from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Union

from babel.numbers import get_currency_precision

if TYPE_CHECKING:
    from django.db.models import Model
    from prices import Money, TaxedMoney, TaxedMoneyRange

MoneyTypes = Union["TaxedMoney", "Money", Decimal, "TaxedMoneyRange"]


def quantize_price(price: MoneyTypes, currency: str) -> MoneyTypes:
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return price.quantize(number_places)


def quantize_price_fields(model: "Model", fields: Iterable[str], currency: str) -> None:
    for field in fields:
        setattr(
            model, field, quantize_price(getattr(model, field) or Decimal(0), currency)
        )
