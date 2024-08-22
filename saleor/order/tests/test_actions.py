from unittest.mock import patch

import pytest

from ...webhook.utils import get_webhooks_for_multiple_events
from .. import OrderStatus
from ..actions import (
    WEBHOOK_EVENTS_FOR_ORDER_CREATED,
    _check_if_fulfillment_quantity_exceeds_order_quantity,
    order_confirmed,
    order_created,
)
from ..fetch import OrderInfo

parametrize_order_statuses = [(status,) for status, _ in OrderStatus.CHOICES]


@pytest.mark.parametrize("order_status", parametrize_order_statuses)
@patch("saleor.order.actions.order_confirmed", wraps=order_confirmed)
def test_order_created_order_confirmed_with_turned_flag_on(
    mock_order_confirmed, order_status, order, customer_user, plugins_manager
):
    # given
    order.status = order_status
    order.save(update_fields=["status"])
    order.channel.automatically_confirm_all_new_orders = True
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    order_info = OrderInfo(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=order.get_last_payment(),
        lines_data=[],
    )

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_CREATED
    )

    # when
    order_created(order_info, user=customer_user, app=None, manager=plugins_manager)

    # then
    mock_order_confirmed.assert_called_once_with(
        order, customer_user, None, plugins_manager, webhook_event_map=webhook_event_map
    )


@pytest.mark.parametrize("order_status", parametrize_order_statuses)
@patch("saleor.order.actions.order_confirmed")
def test_order_created_order_confirmed_with_turned_flag_off(
    mock_order_confirmed, order_status, order, customer_user, plugins_manager
):
    # given
    order.status = order_status
    order.save(update_fields=["status"])
    order.channel.automatically_confirm_all_new_orders = False
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    order_info = OrderInfo(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=order.get_last_payment(),
        lines_data=[],
    )

    # when
    order_created(order_info, user=customer_user, app=None, manager=plugins_manager)

    # then
    mock_order_confirmed.assert_not_called()


@pytest.mark.parametrize(
    ("quantity", "expected_result"), [(5, False), (10, False), (11, True)]
)
def test_check_if_fulfillment_quantity_exceeds_order_quantity(
    quantity, expected_result, order_line
):
    # given
    order_line.quantity_fulfilled = 0
    order_line.quantity = 10

    # when
    result = _check_if_fulfillment_quantity_exceeds_order_quantity(order_line, quantity)

    # then
    assert result is expected_result


@pytest.mark.parametrize(
    ("quantity", "expected_result"), [(5, False), (10, False), (11, True)]
)
def test_check_if_fulfillment_quantity_exceeds_order_quantity_when_no_allocations(
    quantity, expected_result, order_line
):
    # given
    order_line.quantity_fulfilled = 0
    order_line.quantity = 10
    order_line.allocations.all().delete()

    # when
    result = _check_if_fulfillment_quantity_exceeds_order_quantity(order_line, quantity)

    # then
    assert result is expected_result


def test_check_if_fulfillment_quantity_exceeds_order_quantity_when_quantity_fulfilled_is_greater_than_quantity(
    order_line,
):
    # given
    order_line.quantity_fulfilled = 10
    order_line.quantity = 10

    # when
    result = _check_if_fulfillment_quantity_exceeds_order_quantity(order_line, 1)

    # then
    assert result is True
