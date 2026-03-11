from decimal import Decimal
from unittest.mock import Mock

from ..proforma import allocate_costs_to_fulfillments, calculate_fulfillment_total


def _make_order_line(pk, unit_price_gross, quantity):
    line = Mock()
    line.pk = pk
    line.unit_price_gross_amount = unit_price_gross
    line.quantity = quantity
    return line


def _make_fulfillment_line(order_line, quantity):
    line = Mock()
    line.order_line = order_line
    line.order_line_id = order_line.pk
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
    order_lines=None,
):
    order = Mock()
    order.deposit_required = deposit_required
    order.total_deposit_paid = total_deposit_paid
    order.shipping_price_net_amount = shipping_net
    order.currency = currency
    order.fulfillments.all.return_value = all_fulfillments or []
    order.lines.all.return_value = order_lines or []
    return order


def test_single_fulfillment_covers_whole_order():
    """One fulfillment covering whole order gets the entire deposit."""
    ol = _make_order_line(pk="ol1", unit_price_gross=Decimal("100.00"), quantity=3)
    lines = [_make_fulfillment_line(ol, 3)]
    f1 = _make_fulfillment(pk=1, lines=lines)

    order = _make_order(
        total_deposit_paid=Decimal("90.00"),
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1],
        order_lines=[ol],
    )

    allocate_costs_to_fulfillments(order, [f1])

    assert f1.deposit_allocated_amount == Decimal("90.00")
    assert f1.shipping_allocated_net_amount == Decimal("10.00")


def test_partial_fulfillment_gets_proportional_share():
    """Fulfilling half the order gets half the deposit and shipping."""
    ol = _make_order_line(pk="ol1", unit_price_gross=Decimal("50.00"), quantity=2)
    lines = [_make_fulfillment_line(ol, 1)]
    f1 = _make_fulfillment(pk=1, lines=lines)

    order = _make_order(
        total_deposit_paid=Decimal("20.00"),
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1],
        order_lines=[ol],
    )

    allocate_costs_to_fulfillments(order, [f1])

    assert f1.deposit_allocated_amount == Decimal("10.00")
    assert f1.shipping_allocated_net_amount == Decimal("5.00")


def test_second_fulfillment_gets_remainder():
    """F1 already allocated. F2 gets remainder proportional to its share."""
    ol1 = _make_order_line(pk="ol1", unit_price_gross=Decimal("50.00"), quantity=2)
    ol2 = _make_order_line(pk="ol2", unit_price_gross=Decimal("50.00"), quantity=2)

    f1_lines = [_make_fulfillment_line(ol1, 2)]
    f1 = _make_fulfillment(
        pk=1,
        lines=f1_lines,
        deposit_allocated=Decimal("25.00"),
        shipping_allocated_net=Decimal("5.00"),
    )

    f2_lines = [_make_fulfillment_line(ol2, 2)]
    f2 = _make_fulfillment(pk=2, lines=f2_lines)

    order = _make_order(
        total_deposit_paid=Decimal("50.00"),
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1, f2],
        order_lines=[ol1, ol2],
    )

    allocate_costs_to_fulfillments(order, [f2])

    # F2 covers all remaining items, gets all remaining costs
    assert f2.deposit_allocated_amount == Decimal("25.00")
    assert f2.shipping_allocated_net_amount == Decimal("5.00")
    # F1 unchanged
    assert f1.deposit_allocated_amount == Decimal("25.00")
    assert f1.shipping_allocated_net_amount == Decimal("5.00")


def test_two_new_fulfillments_split_remainder_by_weight():
    """Two new fulfillments in same batch split remainder by goods value."""
    ol1 = _make_order_line(pk="ol1", unit_price_gross=Decimal("100.00"), quantity=1)
    ol2 = _make_order_line(pk="ol2", unit_price_gross=Decimal("100.00"), quantity=1)
    ol3 = _make_order_line(pk="ol3", unit_price_gross=Decimal("200.00"), quantity=1)

    f1_lines = [_make_fulfillment_line(ol1, 1)]
    f1 = _make_fulfillment(
        pk=1,
        lines=f1_lines,
        deposit_allocated=Decimal("30.00"),
        shipping_allocated_net=Decimal("5.00"),
    )

    f2_lines = [_make_fulfillment_line(ol2, 1)]
    f2 = _make_fulfillment(pk=2, lines=f2_lines)

    f3_lines = [_make_fulfillment_line(ol3, 1)]
    f3 = _make_fulfillment(pk=3, lines=f3_lines)

    order = _make_order(
        total_deposit_paid=Decimal("90.00"),
        shipping_net=Decimal("15.00"),
        all_fulfillments=[f1, f2, f3],
        order_lines=[ol1, ol2, ol3],
    )

    allocate_costs_to_fulfillments(order, [f2, f3])

    # All items fulfilled (no unfulfilled remainder)
    # Remaining deposit: 90 - 30 = 60, split 1:2 by weight -> 20, 40
    assert f2.deposit_allocated_amount == Decimal("20.00")
    assert f3.deposit_allocated_amount == Decimal("40.00")
    # Remaining shipping: 15 - 5 = 10, split 1:2
    assert (
        f2.shipping_allocated_net_amount + f3.shipping_allocated_net_amount
        == Decimal("10.00")
    )
    # F1 unchanged
    assert f1.deposit_allocated_amount == Decimal("30.00")


def test_no_deposit_required():
    """No deposit -> all fulfillments get 0 deposit."""
    ol = _make_order_line(pk="ol1", unit_price_gross=Decimal("100.00"), quantity=1)
    lines = [_make_fulfillment_line(ol, 1)]
    f1 = _make_fulfillment(pk=1, lines=lines)

    order = _make_order(
        deposit_required=False,
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1],
        order_lines=[ol],
    )

    allocate_costs_to_fulfillments(order, [f1])

    assert f1.deposit_allocated_amount == Decimal(0)
    assert f1.shipping_allocated_net_amount == Decimal("10.00")


def test_deposit_fully_allocated_by_previous():
    """Previous fulfillments already allocated all deposit -> new gets 0."""
    ol1 = _make_order_line(pk="ol1", unit_price_gross=Decimal("100.00"), quantity=1)
    ol2 = _make_order_line(pk="ol2", unit_price_gross=Decimal("100.00"), quantity=1)

    f1 = _make_fulfillment(
        pk=1,
        lines=[_make_fulfillment_line(ol1, 1)],
        deposit_allocated=Decimal("50.00"),
        shipping_allocated_net=Decimal("10.00"),
    )
    f2 = _make_fulfillment(
        pk=2,
        lines=[_make_fulfillment_line(ol2, 1)],
    )

    order = _make_order(
        total_deposit_paid=Decimal("50.00"),
        shipping_net=Decimal("10.00"),
        all_fulfillments=[f1, f2],
        order_lines=[ol1, ol2],
    )

    allocate_costs_to_fulfillments(order, [f2])

    assert f2.deposit_allocated_amount == Decimal(0)
    assert f2.shipping_allocated_net_amount == Decimal(0)


def test_three_sequential_fulfillments_sum_exactly():
    """Three fulfillments created one at a time always sum to total deposit."""
    deposit = Decimal("100.00")
    shipping_net = Decimal("33.33")

    ol1 = _make_order_line(pk="ol1", unit_price_gross=Decimal("100.00"), quantity=1)
    ol2 = _make_order_line(pk="ol2", unit_price_gross=Decimal("200.00"), quantity=1)
    ol3 = _make_order_line(pk="ol3", unit_price_gross=Decimal("300.00"), quantity=1)

    # Round 1: F1 alone
    f1_lines = [_make_fulfillment_line(ol1, 1)]
    f1 = _make_fulfillment(pk=1, lines=f1_lines)

    order = _make_order(
        total_deposit_paid=deposit,
        shipping_net=shipping_net,
        all_fulfillments=[f1],
        order_lines=[ol1, ol2, ol3],
    )
    allocate_costs_to_fulfillments(order, [f1])

    # F1 covers 100/600 of the order
    assert f1.deposit_allocated_amount == Decimal("16.67")
    assert f1.shipping_allocated_net_amount == Decimal("5.56")

    # Round 2: F2 alone
    f2_lines = [_make_fulfillment_line(ol2, 1)]
    f2 = _make_fulfillment(pk=2, lines=f2_lines)
    order.fulfillments.all.return_value = [f1, f2]
    allocate_costs_to_fulfillments(order, [f2])

    # F2 covers 200/500 of remaining order value
    assert f2.deposit_allocated_amount == Decimal("33.33")
    assert f2.shipping_allocated_net_amount == Decimal("11.11")

    # Round 3: F3 alone (last fulfillment, no unfulfilled remainder)
    f3_lines = [_make_fulfillment_line(ol3, 1)]
    f3 = _make_fulfillment(pk=3, lines=f3_lines)
    order.fulfillments.all.return_value = [f1, f2, f3]
    allocate_costs_to_fulfillments(order, [f3])

    # F3 gets all remaining
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
