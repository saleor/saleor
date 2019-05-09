from __future__ import division, unicode_literals

import warnings
from decimal import Decimal
from typing import Union

from .money import Money

Numeric = Union[int, Decimal]


class TaxedMoney:
    """Stores Money for net, gross (incl. tax) and tax."""

    __slots__ = ('net', 'gross')

    def __init__(self, net: Money, gross: Money) -> None:
        if not isinstance(net, Money) or not isinstance(gross, Money):
            raise TypeError('Price requires two amounts, got %r, %r' % (
                net, gross))
        if net.currency != gross.currency:
            raise ValueError(
                'Amounts given in different currencies: %r and %r' % (
                    net.currency, gross.currency))
        self.net = net
        self.gross = gross

    def __repr__(self) -> str:
        return 'TaxedMoney(net=%r, gross=%r)' % (self.net, self.gross)

    def __lt__(self, other: 'TaxedMoney') -> bool:
        if isinstance(other, TaxedMoney):
            return self.gross < other.gross
        elif isinstance(other, Money):
            raise TypeError(
                'Cannot compare taxed and untaxed Money,'
                ' use taxed_money.net or taxed_money.gross explicitly')
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TaxedMoney):
            return (
                self.gross == other.gross and
                self.net == other.net)
        return False

    def __le__(self, other: 'TaxedMoney') -> bool:
        if self == other:
            return True
        return self < other

    def __mul__(self, other: Numeric) -> 'TaxedMoney':
        try:
            net = self.net * other
            gross = self.gross * other
        except TypeError:
            return NotImplemented
        return TaxedMoney(net=net, gross=gross)

    def __rmul__(self, other: Numeric) -> 'TaxedMoney':
        return self * other

    def __truediv__(self, other: Numeric) -> 'TaxedMoney':
        try:
            net = self.net / other
            gross = self.gross / other
        except TypeError:
            return NotImplemented
        return TaxedMoney(net=net, gross=gross)

    def __add__(self, other: Union[Money, 'TaxedMoney']) -> 'TaxedMoney':
        if isinstance(other, TaxedMoney):
            net = self.net + other.net
            gross = self.gross + other.gross
            return TaxedMoney(net=net, gross=gross)
        if isinstance(other, Money):
            net = self.net + other
            gross = self.gross + other
            return TaxedMoney(net=net, gross=gross)
        return NotImplemented

    def __sub__(self, other: Union[Money, 'TaxedMoney']) -> 'TaxedMoney':
        if isinstance(other, TaxedMoney):
            net = self.net - other.net
            gross = self.gross - other.gross
            return TaxedMoney(net=net, gross=gross)
        if isinstance(other, Money):
            net = self.net - other
            gross = self.gross - other
            return TaxedMoney(net=net, gross=gross)
        return NotImplemented

    def __bool__(self) -> bool:  # pragma: no cover
        warnings.warn(
            RuntimeWarning(
                '`bool(taxed_money)` will always evaluate to True, consider'
                ' replacing the test with explicit `if taxed_money is None`'
                ' or `if taxed_money.gross`.'),
            stacklevel=2)
        return True

    @property
    def currency(self) -> str:
        """Return the currency of the money."""
        return self.net.currency

    @property
    def tax(self) -> Money:
        """Return the tax amount."""
        return self.gross - self.net

    def quantize(self, exp=None, rounding=None) -> 'TaxedMoney':
        """Return a new instance with both net and gross quantized.

        All arguments are passed to `Money.quantize`.
        """
        return TaxedMoney(
            net=self.net.quantize(exp, rounding=rounding),
            gross=self.gross.quantize(exp, rounding=rounding))
