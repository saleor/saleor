from prices import TaxedMoney

from ... import base_calculations
from ...interface import OrderTaxedPricesData


def test_base_order_line_total(order_with_lines):
    # given
    line = order_with_lines.lines.all().first()

    # when
    order_total = base_calculations.base_order_line_total(line)

    # then
    base_line_unit_price = line.base_unit_price
    quantity = line.quantity
    expected_price_with_discount = (
        TaxedMoney(base_line_unit_price, base_line_unit_price) * quantity
    )
    base_line_undiscounted_unit_price = line.undiscounted_base_unit_price
    expected_undiscounted_price = (
        TaxedMoney(base_line_undiscounted_unit_price, base_line_undiscounted_unit_price)
        * quantity
    )
    assert order_total == OrderTaxedPricesData(
        price_with_discounts=expected_price_with_discount,
        undiscounted_price=expected_undiscounted_price,
    )
