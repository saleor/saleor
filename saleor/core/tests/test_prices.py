from decimal import Decimal

import pytest

from ..prices import quantize_price


@pytest.mark.parametrize(
    ("price", "currency", "expected_value"),
    [(0, "USD", 0), (Decimal(5), "USD", Decimal(5.00))],
)
def test_quantize_price(price, currency, expected_value):
    price = quantize_price(price, currency)
    assert price == expected_value
