from __future__ import division, unicode_literals

from typing import Union

from .money import Money
from .money_range import MoneyRange
from .taxed_money import TaxedMoney

Addable = Union[Money, MoneyRange, TaxedMoney, 'TaxedMoneyRange']


class TaxedMoneyRange:
    """A taxed money range."""

    __slots__ = ('start', 'stop')

    def __init__(self, start: TaxedMoney, stop: TaxedMoney) -> None:
        if start.currency != stop.currency:
            raise ValueError(
                'Cannot create a range as %r and %r use different currencies' % (
                    start, stop))
        if start > stop:
            raise ValueError(
                'Cannot create a range from %r to %r' % (start, stop))
        self.start = start
        self.stop = stop

    def __repr__(self) -> str:
        return 'TaxedMoneyRange(%r, %r)' % (self.start, self.stop)

    def __add__(self, other: Addable) -> 'TaxedMoneyRange':
        if isinstance(other, (Money, TaxedMoney)):
            if other.currency != self.currency:
                raise ValueError(
                    "Cannot add a range in %r to argument in %r" % (
                        self.currency, other.currency))
            start = self.start + other
            stop = self.stop + other
            return TaxedMoneyRange(start, stop)
        elif isinstance(other, (MoneyRange, TaxedMoneyRange)):
            if other.start.currency != self.currency:
                raise ValueError(
                    'Cannot add ranges in %r and %r' % (
                        self.currency, other.currency))
            start = self.start + other.start
            stop = self.stop + other.stop
            return TaxedMoneyRange(start, stop)
        return NotImplemented

    def __sub__(self, other: Addable) -> 'TaxedMoneyRange':
        if isinstance(other, (Money, TaxedMoney)):
            if other.currency != self.start.currency:
                raise ValueError(
                    'Cannot subtract argument in %r from range in %r' % (
                        other.currency, self.start.currency))
            start = self.start - other
            stop = self.stop - other
            return TaxedMoneyRange(start, stop)
        elif isinstance(other, (MoneyRange, TaxedMoneyRange)):
            if other.start.currency != self.start.currency:
                raise ValueError(
                    'Cannot subtract range in %r from %r' % (
                        other.start.currency, self.start.currency))
            start = self.start - other.start
            stop = self.stop - other.stop
            return TaxedMoneyRange(start, stop)
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TaxedMoneyRange):
            return (
                self.start == other.start and
                self.stop == other.stop)
        return False

    def __contains__(self, item: TaxedMoney) -> bool:
        if not isinstance(item, TaxedMoney):
            raise TypeError(
                '`in taxed_money_range` requires TaxedMoney as left operand, not %s' % (
                    type(item),))
        return self.start <= item <= self.stop

    @property
    def currency(self) -> str:
        """Return the currency of the range."""
        return self.start.currency

    def quantize(self, exp=None, rounding=None) -> 'TaxedMoneyRange':
        """Return a copy of the range with start and stop quantized.

        All arguments are passed to `TaxedMoney.quantize` which in turn calls
        `Money.quantize`.
        """
        return TaxedMoneyRange(
            self.start.quantize(exp, rounding=rounding),
            self.stop.quantize(exp, rounding=rounding))

    def replace(self, start: TaxedMoney = None, stop: TaxedMoney = None) -> 'TaxedMoneyRange':
        """Return a range with start or stop replaced with given values."""
        if start is None:
            start = self.start
        if stop is None:
            stop = self.stop
        return TaxedMoneyRange(start=start, stop=stop)
