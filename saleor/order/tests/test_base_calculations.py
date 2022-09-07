from decimal import Decimal

from prices import Money

from ...discount import DiscountValueType, OrderDiscountType
from .. import base_calculations


def test_base_order_total(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == Money(Decimal("80"), order.currency)


def test_base_order_total_with_voucher(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=10,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == Money(Decimal("70"), order.currency)
