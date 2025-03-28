from enum import Enum

from babel.numbers import list_currencies

CurrencyEnum = Enum(  # type: ignore[misc]
    "CurrencyEnum", {currency: currency for currency in list_currencies()}
)
