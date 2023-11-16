from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from ...tax.calculations import get_taxed_undiscounted_price

BASE = Money("35.00", "USD")


@pytest.mark.parametrize(
    ("price", "tax_rate", "prices_entered_with_tax", "result"),
    [
        # result should not be calculated but taken from price
        (
            TaxedMoney(gross=Money("43.74", "USD"), net=BASE),
            Decimal(0.25),
            False,
            TaxedMoney(gross=Money("43.74", "USD"), net=BASE),
        ),
        # result should be calculated and different from price
        (
            TaxedMoney(gross=Money("43.74", "USD"), net=Money("36.00", "USD")),
            Decimal(0.25),
            False,
            TaxedMoney(gross=Money("43.75", "USD"), net=BASE),
        ),
        # result should not be calculated and taken from price
        (
            TaxedMoney(gross=BASE, net=Money("26.26", "USD")),
            Decimal(0.25),
            True,
            TaxedMoney(gross=BASE, net=Money("26.26", "USD")),
        ),
        # result should be calculated and different from price
        (
            TaxedMoney(gross=Money("36.00", "USD"), net=Money("26.26", "USD")),
            Decimal(0.25),
            True,
            TaxedMoney(gross=BASE, net=Money("28.00", "USD")),
        ),
    ],
)
def test_get_taxed_undiscounted_price(price, tax_rate, prices_entered_with_tax, result):
    result_price = get_taxed_undiscounted_price(
        undiscounted_base_price=BASE,
        price=price,
        tax_rate=tax_rate,
        prices_entered_with_tax=prices_entered_with_tax,
    )

    assert result_price == result
