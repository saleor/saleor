from unittest.mock import patch

import pytest

from .. import OrderStatus
from ..actions import order_created
from ..fetch import OrderInfo

parametrize_order_statuses = [
    (status, flag) for status, _ in OrderStatus.CHOICES for flag in (True, False)
]


@pytest.mark.parametrize(("order_status", "flag"), parametrize_order_statuses)
@patch("saleor.order.actions.order_confirmed")
def test_order_created_order_confirmed(
    mock_order_confirmed, order_status, flag, order, customer_user, plugins_manager
):
    # given
    order.status = order_status
    order.save(update_fields=["status"])
    order.channel.automatically_confirm_all_new_orders = flag
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
    if flag is True:
        mock_order_confirmed.assert_called_once_with(
            order, customer_user, None, plugins_manager
        )
    else:
        mock_order_confirmed.assert_not_called()
