from decimal import Decimal
from typing import Optional, Union, overload

from .money import Money
from .money_range import MoneyRange
from .taxed_money import TaxedMoney
from .taxed_money_range import TaxedMoneyRange

Numeric = Union[int, Decimal]


@overload
def flat_tax(
        base: Union[Money, TaxedMoney],
        tax_rate: Decimal,
        *,
        keep_gross) -> TaxedMoney:
    ...  # pragma: no cover


@overload
def flat_tax(
        base: Union[MoneyRange, TaxedMoneyRange],
        tax_rate: Decimal,
        *,
        keep_gross) -> TaxedMoneyRange:
    ...  # pragma: no cover


def flat_tax(base, tax_rate, *, keep_gross=False):
    """Apply a flat tax by either increasing gross or decreasing net amount."""
    fraction = Decimal(1) + tax_rate
    if isinstance(base, (MoneyRange, TaxedMoneyRange)):
        return TaxedMoneyRange(
            flat_tax(base.start, tax_rate, keep_gross=keep_gross),
            flat_tax(base.stop, tax_rate, keep_gross=keep_gross))
    if isinstance(base, TaxedMoney):
        if keep_gross:
            new_net = (base.net / fraction).quantize()
            return TaxedMoney(net=new_net, gross=base.gross)
        else:
            new_gross = (base.gross * fraction).quantize()
            return TaxedMoney(net=base.net, gross=new_gross)
    if isinstance(base, Money):
        if keep_gross:
            net = (base / fraction).quantize()
            return TaxedMoney(net=net, gross=base)
        else:
            gross = (base * fraction).quantize()
            return TaxedMoney(net=base, gross=gross)
    raise TypeError('Unknown base for flat_tax: %r' % (base,))
