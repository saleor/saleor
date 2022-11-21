from decimal import Decimal

import pytest
from prices import Money

from ...core.prices import quantize_price
from ..calculations import calculate_flat_rate_tax


@pytest.mark.parametrize(
    "amount, net, gross, rate, prices_entered_with_tax",
    [
        ("10.00", "10.00", "12.30", Decimal(23), False),
        ("10.00", "8.13", "10.00", Decimal(23), True),
    ],
)
def test_calculate_flat_tax_rate(amount, net, gross, rate, prices_entered_with_tax):
    currency = "PLN"
    money = Money(amount=amount, currency=currency)
    taxed_money = calculate_flat_rate_tax(money, rate, prices_entered_with_tax)
    assert quantize_price(taxed_money.net.amount, currency) == Decimal(net)
    assert quantize_price(taxed_money.gross.amount, currency) == Decimal(gross)
