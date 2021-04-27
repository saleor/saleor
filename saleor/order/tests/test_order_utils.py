import pytest

from .. import OrderLineData, OrderStatus
from ..events import OrderEvents
from ..models import Order, OrderEvent
from ..utils import (
    change_order_line_quantity,
    get_valid_shipping_methods_for_order,
    match_orders_with_new_user,
)


@pytest.mark.parametrize(
    "status, previous_quantity, new_quantity, added_count, removed_count",
    (
        (OrderStatus.DRAFT, 5, 2, 0, 3),
        (OrderStatus.UNCONFIRMED, 2, 5, 3, 0),
        (OrderStatus.UNCONFIRMED, 2, 0, 0, 2),
        (OrderStatus.DRAFT, 5, 5, 0, 0),
    ),
)
def test_change_quantity_generates_proper_event(
    status,
    previous_quantity,
    new_quantity,
    added_count,
    removed_count,
    order_with_lines,
    staff_user,
):
    assert not OrderEvent.objects.exists()
    order_with_lines.status = status
    order_with_lines.save(update_fields=["status"])

    line = order_with_lines.lines.last()
    line.quantity = previous_quantity
    line_info = OrderLineData(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )
    stock = line.allocations.first().stock
    stock.quantity = 5
    stock.save(update_fields=["quantity"])

    change_order_line_quantity(
        staff_user,
        line_info,
        previous_quantity,
        new_quantity,
        order_with_lines.channel.slug,
    )

    if removed_count:
        expected_type = OrderEvents.REMOVED_PRODUCTS
        expected_quantity = removed_count
    elif added_count:
        expected_type = OrderEvents.ADDED_PRODUCTS
        expected_quantity = added_count
    else:
        # No event should have occurred
        assert not OrderEvent.objects.exists()
        return

    new_event = OrderEvent.objects.last()  # type: OrderEvent
    assert new_event.type == expected_type
    assert new_event.user == staff_user
    assert new_event.parameters == {
        "lines": [
            {"quantity": expected_quantity, "line_pk": line.pk, "item": str(line)}
        ]
    }


def test_match_orders_with_new_user(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()
    order = Order.objects.create(
        billing_address=address,
        user=None,
        user_email=customer_user.email,
        channel=channel_USD,
    )

    match_orders_with_new_user(customer_user)
    order.refresh_from_db()
    assert order.user == customer_user


def test_match_draft_order_with_new_user(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()
    order = Order.objects.create(
        billing_address=address,
        user=None,
        user_email=customer_user.email,
        status=OrderStatus.DRAFT,
        channel=channel_USD,
    )
    match_orders_with_new_user(customer_user)

    order.refresh_from_db()
    assert order.user is None


def test_get_valid_shipping_methods_for_order(order_line_with_one_allocation, address):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(order)

    # then
    assert len(valid_shipping_methods) == 1


def test_get_valid_shipping_methods_for_order_no_channel_shipping_zones(
    order_line_with_one_allocation, address
):
    # given
    order = order_line_with_one_allocation.order
    order.channel.shipping_zones.clear()
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(order)

    # then
    assert len(valid_shipping_methods) == 0


def test_get_valid_shipping_methods_for_order_no_shipping_address(
    order_line_with_one_allocation, address
):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(order)

    # then
    assert valid_shipping_methods is None


def test_get_valid_shipping_methods_for_order_shipping_not_required(
    order_line_with_one_allocation, address
):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = False
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(order)

    # then
    assert valid_shipping_methods is None
