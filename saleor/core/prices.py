from decimal import Decimal
from typing import TYPE_CHECKING, Union

from babel.numbers import get_currency_precision

if TYPE_CHECKING:
    from prices import Money, TaxedMoney, TaxedMoneyRange


def quantize_price(
    price: Union["TaxedMoney", "Money", Decimal, "TaxedMoneyRange"], currency: str
) -> Union["TaxedMoney", "Money", Decimal, "TaxedMoneyRange"]:
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return price.quantize(number_places)
