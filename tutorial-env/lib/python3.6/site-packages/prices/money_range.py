from __future__ import division, unicode_literals

from typing import Union

from .taxed_money import Money

Addable = Union[Money, 'MoneyRange']


class MoneyRange:
    """A taxed money range."""

    __slots__ = ('start', 'stop')

    def __init__(self, start: Money, stop: Money) -> None:
        if start.currency != stop.currency:
            raise ValueError(
                'Cannot create a range as %r and %r use different currencies' % (
                    start, stop))
        if start > stop:
            raise ValueError(
                'Cannot create a range from %r to %r' % (
                    start, stop))
        self.start = start
        self.stop = stop

    def __repr__(self) -> str:
        return 'MoneyRange(%r, %r)' % (self.start, self.stop)

    def __add__(self, other: Addable) -> 'MoneyRange':
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise ValueError(
                    "Cannot add range in %r to argument in %r" % (
                        self.currency, other.currency))
            start = self.start + other
            stop = self.stop + other
            return MoneyRange(start, stop)
        elif isinstance(other, MoneyRange):
            if other.start.currency != self.currency:
                raise ValueError(
                    'Cannot add ranges in %r and %r' % (
                        self.currency, other.currency))
            start = self.start + other.start
            stop = self.stop + other.stop
            return MoneyRange(start, stop)
        return NotImplemented

    def __sub__(self, other: Addable) -> 'MoneyRange':
        if isinstance(other, Money):
            if other.currency != self.start.currency:
                raise ValueError(
                    'Cannot subtract Money in %r from a range in %r' % (
                        other.currency, self.start.currency))
            start = self.start - other
            stop = self.stop - other
            return MoneyRange(start, stop)
        elif isinstance(other, MoneyRange):
            if other.start.currency != self.start.currency:
                raise ValueError(
                    'Cannot subtract range in %r from %r' % (
                        other.start.currency, self.start.currency))
            start = self.start - other.start
            stop = self.stop - other.stop
            return MoneyRange(start, stop)
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MoneyRange):
            return (
                self.start == other.start and
                self.stop == other.stop)
        return False

    def __contains__(self, item: Money) -> bool:
        if not isinstance(item, Money):
            raise TypeError(
                '`in money_range` requires Money as left operand, not %s' % (
                    type(item),))
        return self.start <= item <= self.stop

    @property
    def currency(self) -> str:
        """Return the currency of the range."""
        return self.start.currency

    def quantize(self, exp=None, rounding=None) -> 'MoneyRange':
        """Return a copy of the range with start and stop quantized.

        All arguments are passed to `Money.quantize`.
        """
        return MoneyRange(
            self.start.quantize(exp, rounding=rounding),
            self.stop.quantize(exp, rounding=rounding))

    def replace(self, start: Money = None, stop: Money = None) -> 'MoneyRange':
        """Return a range with start or stop replaced with given values."""
        if start is None:
            start = self.start
        if stop is None:
            stop = self.stop
        return MoneyRange(start=start, stop=stop)
