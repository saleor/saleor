import copy
from decimal import Decimal
from unittest.mock import Mock

import pytest
from prices import Money, TaxedMoney

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCardEvent
from ...order.interface import OrderTaxedPricesData
from ...plugins.manager import get_plugins_manager
from .. import OrderStatus
from ..events import OrderEvents
from ..fetch import OrderLineInfo
from ..models import Order, OrderEvent
from ..utils import (
    add_gift_cards_to_order,
    add_variant_to_order,
    change_order_line_quantity,
    get_valid_shipping_methods_for_order,
    match_orders_with_new_user,
    update_taxes_for_order_line,
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

    line_info = OrderLineInfo(
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
        get_plugins_manager(),
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
    expected_line_pk = None if new_quantity == 0 else str(line.pk)
    assert new_event.parameters == {
        "lines": [
            {
                "quantity": expected_quantity,
                "line_pk": expected_line_pk,
                "item": str(line),
            }
        ]
    }


def test_change_quantity_update_line_fields(
    order_with_lines,
    staff_user,
):
    # given
    line = order_with_lines.lines.last()
    line_info = OrderLineInfo(
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
        get_plugins_manager(),
    )

    # then
    line.refresh_from_db()
    assert line.quantity == new_quantity
    assert line.total_price == line.unit_price * new_quantity
    assert line.undiscounted_total_price == line.undiscounted_unit_price * new_quantity


def test_match_orders_with_new_user(order_list, staff_user, customer_user):
    # given
    for order in order_list[:2]:
        order.user = None
        order.user_email = staff_user.email

    order_with_user = order_list[-1]
    order_with_user.user = customer_user
    order_with_user.user_email = staff_user.email

    Order.objects.bulk_update(order_list, ["user", "user_email"])

    # when
    match_orders_with_new_user(staff_user)

    # then
    for order in order_list[:2]:
        order.refresh_from_db()
        assert order.user == staff_user

    order_with_user.refresh_from_db()
    assert order_with_user.user != staff_user


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
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), get_plugins_manager()
    )

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
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), get_plugins_manager()
    )

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
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), get_plugins_manager()
    )

    # then
    assert valid_shipping_methods == []


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
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), get_plugins_manager()
    )

    # then
    assert valid_shipping_methods == []


def test_update_taxes_for_order_lines(order_with_lines):
    # given
    unit_price = TaxedMoney(net=Money("10.23", "USD"), gross=Money("15.80", "USD"))
    total_price = TaxedMoney(net=Money("30.34", "USD"), gross=Money("36.49", "USD"))
    tax_rate = Decimal("0.23")
    unit_price_data = OrderTaxedPricesData(
        undiscounted_price=unit_price,
        price_with_discounts=unit_price,
    )
    total_price_data = OrderTaxedPricesData(
        undiscounted_price=total_price,
        price_with_discounts=total_price,
    )
    manager = Mock(
        calculate_order_line_unit=Mock(return_value=unit_price_data),
        calculate_order_line_total=Mock(return_value=total_price_data),
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
        assert line.undiscounted_unit_price == unit_price
        assert line.undiscounted_total_price == total_price


def test_update_taxes_for_order_lines_discounted_price(order_with_lines):
    # given
    unit_discount_amount = Decimal("2.00")

    unit_price = TaxedMoney(net=Money("10.23", "USD"), gross=Money("15.80", "USD"))
    total_price = TaxedMoney(net=Money("30.34", "USD"), gross=Money("36.49", "USD"))
    tax_rate = Decimal("0.23")
    discount = TaxedMoney(
        net=Money(unit_discount_amount, "USD"), gross=Money(unit_discount_amount, "USD")
    )
    unit_price_data = OrderTaxedPricesData(
        undiscounted_price=unit_price + discount,
        price_with_discounts=unit_price,
    )
    total_price_data = OrderTaxedPricesData(
        undiscounted_price=total_price + discount,
        price_with_discounts=total_price,
    )
    manager = Mock(
        calculate_order_line_unit=Mock(return_value=unit_price_data),
        calculate_order_line_total=Mock(return_value=total_price_data),
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
        assert line.undiscounted_unit_price == unit_price + discount
        assert line.undiscounted_total_price == total_price + discount


def test_add_variant_to_order(order, customer_user, variant, site_settings):
    # given
    unit_price = TaxedMoney(net=Money("10.23", "USD"), gross=Money("15.80", "USD"))
    total_price = TaxedMoney(net=Money("30.34", "USD"), gross=Money("36.49", "USD"))
    tax_rate = Decimal("0.23")
    unit_price_data = OrderTaxedPricesData(
        undiscounted_price=unit_price,
        price_with_discounts=unit_price,
    )
    total_price_data = OrderTaxedPricesData(
        undiscounted_price=total_price,
        price_with_discounts=total_price,
    )
    manager = Mock(
        calculate_order_line_unit=Mock(return_value=unit_price_data),
        calculate_order_line_total=Mock(return_value=total_price_data),
        get_order_line_tax_rate=Mock(return_value=tax_rate),
    )
    app = None

    # when
    line = add_variant_to_order(
        order, variant, 4, customer_user, app, manager, site_settings
    )

    # then
    assert line.unit_price == unit_price
    assert line.total_price == total_price
    assert line.undiscounted_unit_price == unit_price
    assert line.undiscounted_total_price == total_price
    assert line.tax_rate == tax_rate


def test_add_gift_cards_to_order(
    checkout_with_item, gift_card, gift_card_expiry_date, order, staff_user
):
    # given
    checkout = checkout_with_item
    checkout.user = staff_user
    checkout.gift_cards.add(gift_card, gift_card_expiry_date)
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    add_gift_cards_to_order(
        checkout_info, order, Money(20, gift_card.currency), staff_user, None
    )

    # then
    gift_card.refresh_from_db()
    gift_card_expiry_date.refresh_from_db()
    assert gift_card.current_balance_amount == 0
    assert gift_card_expiry_date.current_balance_amount == 0
    assert gift_card.used_by == staff_user
    assert gift_card.used_by_email == staff_user.email

    gift_card_events = GiftCardEvent.objects.filter(gift_card_id=gift_card.id)
    assert gift_card_events.count() == 1
    gift_card_event = gift_card_events[0]
    assert gift_card_event.type == GiftCardEvents.USED_IN_ORDER
    assert gift_card_event.user == staff_user
    assert gift_card_event.app is None
    assert gift_card_event.order == order
    assert gift_card_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "10.000",
        },
    }

    order_created_event = GiftCardEvent.objects.get(
        gift_card_id=gift_card_expiry_date.id
    )
    assert order_created_event.user == staff_user
    assert order_created_event.app is None
    assert order_created_event.order == order
    assert order_created_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "20.000",
        },
    }


def test_add_gift_cards_to_order_no_checkout_user(
    checkout_with_item, gift_card, gift_card_expiry_date, order, staff_user
):
    # given
    checkout = checkout_with_item
    checkout.user = None
    checkout.email = staff_user.email
    checkout.save(update_fields=["user", "email"])

    checkout.gift_cards.add(gift_card, gift_card_expiry_date)
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    add_gift_cards_to_order(
        checkout_info, order, Money(20, gift_card.currency), staff_user, None
    )

    # then
    gift_card.refresh_from_db()
    gift_card_expiry_date.refresh_from_db()
    assert gift_card.current_balance_amount == 0
    assert gift_card_expiry_date.current_balance_amount == 0
    assert gift_card.used_by == staff_user
    assert gift_card.used_by_email == staff_user.email

    gift_card_events = GiftCardEvent.objects.filter(gift_card_id=gift_card.id)
    assert gift_card_events.count() == 1
    gift_card_event = gift_card_events[0]
    assert gift_card_event.type == GiftCardEvents.USED_IN_ORDER
    assert gift_card_event.user == staff_user
    assert gift_card_event.app is None
    assert gift_card_event.order == order
    assert gift_card_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "10.000",
        },
    }

    order_created_event = GiftCardEvent.objects.get(
        gift_card_id=gift_card_expiry_date.id
    )
    assert order_created_event.user == staff_user
    assert order_created_event.app is None
    assert order_created_event.order == order
    assert order_created_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "20.000",
        },
    }


def test_update_taxes_for_order_line_deleted_variant(order_with_lines):
    # given
    order_line = order_with_lines.lines.first()
    order_line_unchanged_copy = copy.deepcopy(order_line)
    unit_discount_amount = Decimal("2.00")

    unit_price = TaxedMoney(net=Money("10.23", "USD"), gross=Money("15.80", "USD"))
    total_price = TaxedMoney(net=Money("30.34", "USD"), gross=Money("36.49", "USD"))
    tax_rate = Decimal("0.23")
    discount = TaxedMoney(
        net=Money(unit_discount_amount, "USD"), gross=Money(unit_discount_amount, "USD")
    )
    unit_price_data = OrderTaxedPricesData(
        undiscounted_price=unit_price + discount,
        price_with_discounts=unit_price,
    )
    total_price_data = OrderTaxedPricesData(
        undiscounted_price=total_price + discount,
        price_with_discounts=total_price,
    )
    manager = Mock(
        calculate_order_line_unit=Mock(return_value=unit_price_data),
        calculate_order_line_total=Mock(return_value=total_price_data),
        get_order_line_tax_rate=Mock(return_value=tax_rate),
    )

    # when
    order_line.variant = None
    update_taxes_for_order_line(order_line, order_with_lines, manager, True)

    # then
    assert order_line.unit_price == order_line_unchanged_copy.unit_price
    assert order_line.total_price == order_line_unchanged_copy.total_price
    assert order_line.tax_rate == order_line_unchanged_copy.tax_rate
    assert order_line.undiscounted_unit_price == order_line_unchanged_copy.unit_price
    assert order_line.undiscounted_total_price == order_line_unchanged_copy.total_price
