from decimal import Decimal
from unittest.mock import Mock

from ..proforma import (
    calculate_deposit_allocation,
    calculate_fulfillment_total,
    calculate_proportional_shipping,
)


def _make_order_line(quantity, quantity_fulfilled):
    line = Mock()
    line.quantity = quantity
    line.quantity_fulfilled = quantity_fulfilled
    line.quantity_unfulfilled = quantity - quantity_fulfilled
    return line


def _make_order(
    deposit_required=True,
    total_deposit_paid=Decimal(0),
    total_gross_amount=Decimal(0),
    fulfillments=None,
    lines=None,
):
    order = Mock()
    order.deposit_required = deposit_required
    order.total_deposit_paid = total_deposit_paid
    order.total_gross_amount = total_gross_amount
    order.fulfillments.all.return_value = fulfillments or []
    order.lines.all.return_value = lines or []
    return order


def test_no_deposit():
    order = _make_order(deposit_required=False)

    result = calculate_deposit_allocation(order, Decimal(100))

    assert result == Decimal(0)


def test_zero_deposit_paid():
    order = _make_order(total_deposit_paid=Decimal(0), total_gross_amount=Decimal(200))

    result = calculate_deposit_allocation(order, Decimal(100))

    assert result == Decimal(0)


def test_zero_order_total():
    order = _make_order(total_deposit_paid=Decimal(50), total_gross_amount=Decimal(0))

    result = calculate_deposit_allocation(order, Decimal(100))

    assert result == Decimal(0)


def test_simple_allocation():
    order = _make_order(
        total_deposit_paid=Decimal(100),
        total_gross_amount=Decimal(200),
        lines=[_make_order_line(10, 5)],
    )

    result = calculate_deposit_allocation(order, Decimal(50))

    assert result == Decimal("25.00")


def test_result_is_quantized_to_2dp():
    order = _make_order(
        total_deposit_paid=Decimal(100),
        total_gross_amount=Decimal(300),
        lines=[_make_order_line(9, 3)],
    )

    result = calculate_deposit_allocation(order, Decimal(100))

    # 100 * 100/300 = 33.333... → quantized to 33.33
    assert result == Decimal("33.33")
    assert result == result.quantize(Decimal("0.01"))


def test_remaining_less_than_proportional():
    existing = Mock()
    existing.deposit_allocated_amount = Decimal(90)
    order = _make_order(
        total_deposit_paid=Decimal(100),
        total_gross_amount=Decimal(200),
        fulfillments=[existing],
        lines=[_make_order_line(10, 5)],
    )

    result = calculate_deposit_allocation(order, Decimal(100))

    assert result == Decimal("10.00")


def test_last_fulfillment_gets_remainder():
    # 3 equal fulfillments, deposit doesn't divide evenly by 3.
    # Last fulfillment should get remainder so sum is exact.
    order = _make_order(
        total_deposit_paid=Decimal("100.00"),
        total_gross_amount=Decimal("300.00"),
    )

    allocated = []
    for i in range(3):
        order.fulfillments.all.return_value = [
            Mock(deposit_allocated_amount=d) for d in allocated
        ]
        # After each fulfillment, update lines to reflect fulfilled quantities.
        # 3 lines of qty=1 each, fulfilled one at a time.
        is_last = i == 2
        order.lines.all.return_value = (
            [_make_order_line(1, 1 if j <= i else 0) for j in range(3)]
            if is_last
            else [_make_order_line(1, 1 if j <= i else 0) for j in range(3)]
        )
        # Simpler: on last iteration all 3 lines are fulfilled
        order.lines.all.return_value = [
            _make_order_line(1, 1) if j <= i else _make_order_line(1, 0)
            for j in range(3)
        ]
        deposit = calculate_deposit_allocation(order, Decimal("100.00"))
        allocated.append(deposit)

    assert sum(allocated) == Decimal("100.00")
    # First two get 33.33, last gets 33.34
    assert allocated[0] == Decimal("33.33")
    assert allocated[1] == Decimal("33.33")
    assert allocated[2] == Decimal("33.34")


def test_last_fulfillment_gets_remainder_uneven_split():
    # Order £700, deposit £200, two fulfillments of £400 and £300.
    # proportional: 400*200/700 = 114.2857... → 114.29
    #               300*200/700 = 85.7142...  → 85.71
    # Sum without remainder: 114.29 + 85.71 = 200.00 (happens to be exact here)
    # But let's use numbers that don't work out:
    # Order £1000, deposit £333, three fulfillments of £400, £350, £250
    order = _make_order(
        total_deposit_paid=Decimal("333.00"),
        total_gross_amount=Decimal("1000.00"),
    )

    fulfillment_totals = [Decimal("400.00"), Decimal("350.00"), Decimal("250.00")]
    allocated = []

    for i, ft in enumerate(fulfillment_totals):
        order.fulfillments.all.return_value = [
            Mock(deposit_allocated_amount=d) for d in allocated
        ]
        is_last = i == len(fulfillment_totals) - 1
        order.lines.all.return_value = [
            _make_order_line(1, 1) if is_last else _make_order_line(1, 0)
        ]
        deposit = calculate_deposit_allocation(order, ft)
        allocated.append(deposit)

    assert sum(allocated) == Decimal("333.00")


def test_single_fulfillment_full_order():
    order = _make_order(
        total_deposit_paid=Decimal("62.56"),
        total_gross_amount=Decimal("125.12"),
        lines=[_make_order_line(3, 3)],
    )

    result = calculate_deposit_allocation(order, Decimal("125.12"))

    assert result == Decimal("62.56")


def test_two_partial_fulfillments_with_proportional_shipping():
    # Order: 3 × £37.64 = £112.92 lines, £12.20 shipping = £125.12 total
    # Deposit: 50% = £62.56
    order = _make_order(
        total_deposit_paid=Decimal("62.56"),
        total_gross_amount=Decimal("125.12"),
    )

    shipping = Decimal("12.20")
    order_lines_total = Decimal("112.92")

    # Fulfillment 1: 2 products
    order.fulfillments.all.return_value = []
    order.lines.all.return_value = [_make_order_line(3, 2)]
    f1_lines = Decimal("75.28")
    prop_shipping_1 = calculate_proportional_shipping(
        shipping, f1_lines, order_lines_total
    )
    deposit_1 = calculate_deposit_allocation(order, f1_lines + prop_shipping_1)

    # Fulfillment 2: 1 product (last)
    f1 = Mock()
    f1.deposit_allocated_amount = deposit_1
    order.fulfillments.all.return_value = [f1]
    order.lines.all.return_value = [_make_order_line(3, 3)]
    f2_lines = Decimal("37.64")
    prop_shipping_2 = calculate_proportional_shipping(
        shipping, f2_lines, order_lines_total
    )
    deposit_2 = calculate_deposit_allocation(order, f2_lines + prop_shipping_2)

    assert deposit_1 + deposit_2 == Decimal("62.56")


def test_three_equal_fulfillments_with_shipping():
    order = _make_order(
        total_deposit_paid=Decimal("30.00"),
        total_gross_amount=Decimal("120.00"),
    )

    shipping = Decimal("30.00")
    order_lines_total = Decimal("90.00")

    allocated = []
    for i in range(3):
        order.fulfillments.all.return_value = [
            Mock(deposit_allocated_amount=d) for d in allocated
        ]
        is_last = i == 2
        order.lines.all.return_value = [
            _make_order_line(3, 3) if is_last else _make_order_line(3, i + 1)
        ]
        f_lines = Decimal("30.00")
        prop_shipping = calculate_proportional_shipping(
            shipping, f_lines, order_lines_total
        )
        deposit = calculate_deposit_allocation(order, f_lines + prop_shipping)
        allocated.append(deposit)

    assert sum(allocated) == Decimal("30.00")
    for deposit in allocated:
        assert deposit == Decimal("10.00")


def test_proportional_shipping_full_fulfillment():
    result = calculate_proportional_shipping(
        shipping_amount=Decimal("12.20"),
        fulfillment_lines_total=Decimal("112.92"),
        order_lines_total=Decimal("112.92"),
    )
    assert result == Decimal("12.20")


def test_proportional_shipping_partial_fulfillment():
    result = calculate_proportional_shipping(
        shipping_amount=Decimal("12.00"),
        fulfillment_lines_total=Decimal("75.28"),
        order_lines_total=Decimal("112.92"),
    )
    assert result == Decimal("12.00") * Decimal("75.28") / Decimal("112.92")


def test_proportional_shipping_zero_order_lines():
    result = calculate_proportional_shipping(
        shipping_amount=Decimal("12.20"),
        fulfillment_lines_total=Decimal(0),
        order_lines_total=Decimal(0),
    )
    assert result == Decimal(0)


def test_proportional_shipping_two_partials_sum_to_full():
    shipping = Decimal("12.00")
    order_lines_total = Decimal("112.92")
    f1_lines = Decimal("75.28")
    f2_lines = Decimal("37.64")

    share1 = calculate_proportional_shipping(shipping, f1_lines, order_lines_total)
    share2 = calculate_proportional_shipping(shipping, f2_lines, order_lines_total)

    assert share1 + share2 == shipping


def test_fulfillment_total():
    line1 = Mock()
    line1.order_line.unit_price_gross_amount = Decimal(10)
    line1.quantity = 2

    line2 = Mock()
    line2.order_line.unit_price_gross_amount = Decimal(25)
    line2.quantity = 3

    fulfillment = Mock()
    fulfillment.lines.all.return_value = [line1, line2]

    result = calculate_fulfillment_total(fulfillment)

    assert result == Decimal(95)
