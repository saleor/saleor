from decimal import Decimal, ROUND_DOWN
from typing import TypeVar, Union

from .money import Money
from .money_range import MoneyRange
from .taxed_money import TaxedMoney
from .taxed_money_range import TaxedMoneyRange

Numeric = Union[int, Decimal]

T = TypeVar('T', Money, MoneyRange, TaxedMoney, TaxedMoneyRange)


def fixed_discount(base: T, discount: Money) -> T:
    """Apply a fixed discount to any price type."""
    if isinstance(base, MoneyRange):
        return MoneyRange(
            fixed_discount(base.start, discount),
            fixed_discount(base.stop, discount))
    if isinstance(base, TaxedMoneyRange):
        return TaxedMoneyRange(
            fixed_discount(base.start, discount),
            fixed_discount(base.stop, discount))
    if isinstance(base, TaxedMoney):
        return TaxedMoney(
            net=fixed_discount(base.net, discount),
            gross=fixed_discount(base.gross, discount))
    if isinstance(base, Money):
        return max(base - discount, Money(0, base.currency))
    raise TypeError('Unknown base for fixed_discount: %r' % (base,))


def fractional_discount(base: T, fraction: Decimal, *, from_gross=True) -> T:
    """Apply a fractional discount based on either gross or net amount."""
    if isinstance(base, MoneyRange):
        return MoneyRange(
            fractional_discount(base.start, fraction, from_gross=from_gross),
            fractional_discount(base.stop, fraction, from_gross=from_gross))
    if isinstance(base, TaxedMoneyRange):
        return TaxedMoneyRange(
            fractional_discount(base.start, fraction, from_gross=from_gross),
            fractional_discount(base.stop, fraction, from_gross=from_gross))
    if isinstance(base, TaxedMoney):
        if from_gross:
            discount = (base.gross * fraction).quantize(rounding=ROUND_DOWN)
        else:
            discount = (base.net * fraction).quantize(rounding=ROUND_DOWN)
        return fixed_discount(base, discount)
    if isinstance(base, Money):
        discount = (base * fraction).quantize(rounding=ROUND_DOWN)
        return fixed_discount(base, discount)
    raise TypeError('Unknown base for fractional_discount: %r' % (base,))


def percentage_discount(base: T, percentage: Numeric, *, from_gross=True) -> T:
    """Apply a percentage discount based on either gross or net amount."""
    factor = Decimal(percentage) / 100
    return fractional_discount(base, factor, from_gross=from_gross)
