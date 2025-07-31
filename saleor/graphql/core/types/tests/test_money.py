from decimal import Decimal

from prices import Money

from ..money import Money as MoneyObject


def test_money_object_usd():
    money = Money(Decimal("12.950000"), "USD")
    resolve_info = None

    assert MoneyObject.resolve_amount(money, resolve_info) == Decimal("12.95")
    assert MoneyObject.resolve_fractional_amount(money, resolve_info) == 1295
    assert MoneyObject.resolve_fraction_digits(money, resolve_info) == 2


def test_money_object_jpy():
    money = Money(Decimal(1234), "JPY")
    resolve_info = None

    assert MoneyObject.resolve_amount(money, resolve_info) == Decimal(1234)
    assert MoneyObject.resolve_fractional_amount(money, resolve_info) == 1234
    assert MoneyObject.resolve_fraction_digits(money, resolve_info) == 0
