from decimal import Decimal
from unittest.mock import Mock

from ..proforma import allocate_costs_to_fulfillments, calculate_fulfillment_total


def _make_fulfillment_line(unit_price_gross, quantity):
    line = Mock()
    line.order_line.unit_price_gross_amount = unit_price_gross
    line.quantity = quantity
    return line


def _make_fulfillment(
    pk, lines, deposit_allocated=Decimal(0), shipping_allocated_net=Decimal(0)
):
    f = Mock()
    f.pk = pk
    f.lines.all.return_value = lines
    f.deposit_allocated_amount = deposit_allocated
    f.shipping_allocated_net_amount = shipping_allocated_net
    return f


def _make_order(
    deposit_required=True,
    total_deposit_paid=Decimal(0),
    shipping_net=Decimal(0),
    currency="GBP",
    all_fulfillments=None,
):
    order = Mock()
    order.deposit_required = deposit_required
    order.total_deposit_paid = total_deposit_paid
    order.shipping_price_net_amount = shipping_net
    order.currency = currency
    order.fulfillments.all.return_value = all_fulfillments or []
    return order


def test_single_fulfillment_gets_full_deposit():
    """One fulfillment covering whole order gets the entire deposit."""
    lines = [_make_fulfillment_line(Decimal("100.00"), 3)]
    f1 = _make_fulfillment(pk=1, lines=lines)

    order = _make_order(
        total_deposit_paid=Decimal("90.00"),
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1],
    )

    allocate_costs_to_fulfillments(order, [f1])

    assert f1.deposit_allocated_amount == Decimal("90.00")
    assert f1.shipping_allocated_net_amount == Decimal("10.00")


def test_second_fulfillment_gets_remainder():
    """F1 already allocated. F2 gets whatever deposit is left."""
    f1_lines = [_make_fulfillment_line(Decimal("50.00"), 2)]
    f1 = _make_fulfillment(
        pk=1,
        lines=f1_lines,
        deposit_allocated=Decimal("30.00"),
        shipping_allocated_net=Decimal("6.00"),
    )

    f2_lines = [_make_fulfillment_line(Decimal("50.00"), 2)]
    f2 = _make_fulfillment(pk=2, lines=f2_lines)

    order = _make_order(
        total_deposit_paid=Decimal("50.00"),
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1, f2],
    )

    allocate_costs_to_fulfillments(order, [f2])

    # F1 had 30, total is 50, so F2 gets remaining 20
    assert f2.deposit_allocated_amount == Decimal("20.00")
    # F1 had 6, total shipping is 10, so F2 gets remaining 4
    assert f2.shipping_allocated_net_amount == Decimal("4.00")
    # F1 unchanged
    assert f1.deposit_allocated_amount == Decimal("30.00")
    assert f1.shipping_allocated_net_amount == Decimal("6.00")


def test_two_new_fulfillments_split_remainder_by_weight():
    """Two new fulfillments in same batch split remainder by goods value."""
    f1_lines = [_make_fulfillment_line(Decimal("100.00"), 1)]
    f1 = _make_fulfillment(
        pk=1,
        lines=f1_lines,
        deposit_allocated=Decimal("30.00"),
        shipping_allocated_net=Decimal("5.00"),
    )

    f2_lines = [_make_fulfillment_line(Decimal("100.00"), 1)]  # £100
    f2 = _make_fulfillment(pk=2, lines=f2_lines)

    f3_lines = [_make_fulfillment_line(Decimal("200.00"), 1)]  # £200
    f3 = _make_fulfillment(pk=3, lines=f3_lines)

    order = _make_order(
        total_deposit_paid=Decimal("90.00"),
        shipping_net=Decimal("15.00"),
        all_fulfillments=[f1, f2, f3],
    )

    allocate_costs_to_fulfillments(order, [f2, f3])

    # Remaining deposit: 90 - 30 = 60, split 1:2 by weight → 20, 40
    assert f2.deposit_allocated_amount == Decimal("20.00")
    assert f3.deposit_allocated_amount == Decimal("40.00")
    # Remaining shipping: 15 - 5 = 10, split 1:2 → 3.33, 6.67
    assert (
        f2.shipping_allocated_net_amount + f3.shipping_allocated_net_amount
        == Decimal("10.00")
    )
    # F1 unchanged
    assert f1.deposit_allocated_amount == Decimal("30.00")


def test_no_deposit_required():
    """No deposit → all fulfillments get 0 deposit."""
    lines = [_make_fulfillment_line(Decimal("100.00"), 1)]
    f1 = _make_fulfillment(pk=1, lines=lines)

    order = _make_order(
        deposit_required=False,
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1],
    )

    allocate_costs_to_fulfillments(order, [f1])

    assert f1.deposit_allocated_amount == Decimal(0)
    assert f1.shipping_allocated_net_amount == Decimal("10.00")


def test_deposit_fully_allocated_by_previous():
    """Previous fulfillments already allocated all deposit → new gets 0."""
    f1 = _make_fulfillment(
        pk=1,
        lines=[_make_fulfillment_line(Decimal("100.00"), 1)],
        deposit_allocated=Decimal("50.00"),
        shipping_allocated_net=Decimal("10.00"),
    )
    f2 = _make_fulfillment(
        pk=2,
        lines=[_make_fulfillment_line(Decimal("100.00"), 1)],
    )

    order = _make_order(
        total_deposit_paid=Decimal("50.00"),
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1, f2],
    )

    allocate_costs_to_fulfillments(order, [f2])

    assert f2.deposit_allocated_amount == Decimal(0)
    assert f2.shipping_allocated_net_amount == Decimal(0)


def test_three_sequential_fulfillments_sum_exactly():
    """Three fulfillments created one at a time always sum to total deposit."""
    deposit = Decimal("100.00")
    shipping_net = Decimal("33.33")

    # Simulate creating 3 fulfillments one at a time
    f1_lines = [_make_fulfillment_line(Decimal("100.00"), 1)]
    f1 = _make_fulfillment(pk=1, lines=f1_lines)

    order = _make_order(
        total_deposit_paid=deposit,
        shipping_net=shipping_net,
        all_fulfillments=[f1],
    )
    allocate_costs_to_fulfillments(order, [f1])

    f2_lines = [_make_fulfillment_line(Decimal("200.00"), 1)]
    f2 = _make_fulfillment(pk=2, lines=f2_lines)
    order.fulfillments.all.return_value = [f1, f2]
    allocate_costs_to_fulfillments(order, [f2])

    f3_lines = [_make_fulfillment_line(Decimal("300.00"), 1)]
    f3 = _make_fulfillment(pk=3, lines=f3_lines)
    order.fulfillments.all.return_value = [f1, f2, f3]
    allocate_costs_to_fulfillments(order, [f3])

    total_dep = (
        f1.deposit_allocated_amount
        + f2.deposit_allocated_amount
        + f3.deposit_allocated_amount
    )
    assert total_dep == deposit

    total_ship = (
        f1.shipping_allocated_net_amount
        + f2.shipping_allocated_net_amount
        + f3.shipping_allocated_net_amount
    )
    assert total_ship == shipping_net


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
