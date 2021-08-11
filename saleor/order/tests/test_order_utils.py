from decimal import Decimal
from unittest.mock import Mock

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from prices import Money, TaxedMoney

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCardEvent
from ...plugins.manager import get_plugins_manager
from .. import OrderLineData, OrderStatus
from ..events import OrderEvents
from ..models import Order, OrderEvent
from ..utils import (
    add_gift_cards_to_order,
    add_variant_to_order,
    change_order_line_quantity,
    get_valid_shipping_methods_for_order,
    match_orders_with_new_user,
    update_taxes_for_order_lines,
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
    app = None

    change_order_line_quantity(
        staff_user,
        app,
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


def test_change_quantity_update_line_fields(
    order_with_lines,
    staff_user,
):
    # given
    line = order_with_lines.lines.last()
    line_info = OrderLineData(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )
    new_quantity = 5
    app = None

    # when
    change_order_line_quantity(
        staff_user,
        app,
        line_info,
        line.quantity,
        new_quantity,
        order_with_lines.channel.slug,
    )

    # then
    line.refresh_from_db()
    assert line.quantity == new_quantity
    assert line.total_price == line.unit_price * new_quantity
    assert line.undiscounted_total_price == line.undiscounted_unit_price * new_quantity


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


def test_update_taxes_for_order_lines(order_with_lines):
    # given
    line_with_discount = order_with_lines.lines.first()
    line_with_discount.unit_discount_amount = Decimal("2.00")
    line_with_discount.save(update_fields=["unit_discount_amount"])

    unit_price = TaxedMoney(net=Money("10.23", "USD"), gross=Money("15.80", "USD"))
    total_price = TaxedMoney(net=Money("30.34", "USD"), gross=Money("36.49", "USD"))
    tax_rate = Decimal("0.23")
    manager = Mock(
        calculate_order_line_unit=Mock(return_value=unit_price),
        calculate_order_line_total=Mock(return_value=total_price),
        get_order_line_tax_rate=Mock(return_value=tax_rate),
    )

    # when
    update_taxes_for_order_lines(
        order_with_lines.lines.all(), order_with_lines, manager, True
    )

    # then
    for line in order_with_lines.lines.all():
        assert line.unit_price == unit_price
        assert line.total_price == total_price
        assert line.tax_rate == tax_rate
        if line.pk != line_with_discount.pk:
            assert line.undiscounted_unit_price == unit_price
            assert line.undiscounted_total_price == total_price
        else:
            assert line.undiscounted_unit_price == unit_price + line.unit_discount
            assert (
                line.undiscounted_total_price
                == (unit_price + line.unit_discount) * line.quantity
            )


def test_add_variant_to_order(order, customer_user, variant):
    # given
    unit_price = TaxedMoney(net=Money("10.23", "USD"), gross=Money("15.80", "USD"))
    total_price = TaxedMoney(net=Money("30.34", "USD"), gross=Money("36.49", "USD"))
    tax_rate = Decimal("0.23")
    manager = Mock(
        calculate_order_line_unit=Mock(return_value=unit_price),
        calculate_order_line_total=Mock(return_value=total_price),
        get_order_line_tax_rate=Mock(return_value=tax_rate),
    )
    app = None

    # when
    line = add_variant_to_order(order, variant, 4, customer_user, app, manager)

    # then
    assert line.unit_price == unit_price
    assert line.total_price == total_price
    assert line.undiscounted_unit_price == unit_price
    assert line.undiscounted_total_price == total_price
    assert line.tax_rate == tax_rate


def test_add_gift_cards_to_order(
    checkout_with_item, gift_card, gift_card_expiry_period, order, staff_user
):
    # given
    checkout = checkout_with_item
    checkout.gift_cards.add(gift_card, gift_card_expiry_period)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    add_gift_cards_to_order(
        checkout_info, order, Money(20, gift_card.currency), staff_user, None
    )

    # then
    gift_card.refresh_from_db()
    gift_card_expiry_period.refresh_from_db()
    assert gift_card.current_balance_amount == 0
    assert gift_card_expiry_period.current_balance_amount == 0

    gift_card_events = GiftCardEvent.objects.filter(gift_card_id=gift_card.id)
    assert gift_card_events.count() == 1
    gift_card_event = gift_card_events[0]
    assert gift_card_event.type == GiftCardEvents.USED_IN_ORDER
    assert gift_card_event.user == staff_user
    assert gift_card_event.app is None
    assert gift_card_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "10.000",
        },
        "order_id": order.id,
    }

    gift_card_expiry_period_events = GiftCardEvent.objects.filter(
        gift_card_id=gift_card_expiry_period.id
    )
    assert len(gift_card_expiry_period_events) == 2
    order_created_event = gift_card_expiry_period_events.get(
        type=GiftCardEvents.USED_IN_ORDER
    )
    assert order_created_event.user == staff_user
    assert order_created_event.app is None
    assert order_created_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "10.000",
        },
        "order_id": order.id,
    }
    expiry_date_set_event = gift_card_expiry_period_events.get(
        type=GiftCardEvents.EXPIRY_DATE_SET
    )
    assert expiry_date_set_event.user == staff_user
    assert expiry_date_set_event.app is None
    assert expiry_date_set_event.parameters == {
        "expiry": {
            "expiry_date": (timezone.now().date() + relativedelta(years=2)).isoformat()
        }
    }
