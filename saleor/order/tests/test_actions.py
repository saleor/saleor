from unittest.mock import patch

import pytest

from .. import OrderStatus
from ..actions import order_created
from ..fetch import OrderInfo

parametrize_order_statuses = [(status,) for status, _ in OrderStatus.CHOICES]


@pytest.mark.parametrize("order_status", parametrize_order_statuses)
@patch("saleor.order.actions.order_confirmed")
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

    # when
    order_created(order_info, user=customer_user, app=None, manager=plugins_manager)

    # then
    mock_order_confirmed.assert_called_once_with(
        order, customer_user, None, plugins_manager
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
