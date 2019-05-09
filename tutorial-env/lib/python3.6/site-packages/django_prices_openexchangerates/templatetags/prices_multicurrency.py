from typing import TypeVar

from django.template import Library
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from .. import exchange_currency

T = TypeVar('T', Money, MoneyRange, TaxedMoney, TaxedMoneyRange)

register = Library()


@register.filter
def in_currency(base: T, currency: str) -> T:
    converted_base = exchange_currency(base, currency)
    return converted_base.quantize()
