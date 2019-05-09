"""prices.

Provides a Pythonic interface to deal with money types such as money amounts,
prices, discounts and taxes.
"""
from .discount import (
    fixed_discount, fractional_discount, percentage_discount)
from .money import Money
from .money_range import MoneyRange
from .tax import flat_tax
from .taxed_money import TaxedMoney
from .taxed_money_range import TaxedMoneyRange
from .utils import sum

__all__ = [
    'Money', 'MoneyRange', 'TaxedMoney', 'TaxedMoneyRange', 'fixed_discount',
    'flat_tax', 'fractional_discount', 'percentage_discount', 'sum']
