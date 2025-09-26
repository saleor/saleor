from unittest.mock import patch

import pytest

from ...graphql.core.utils import to_global_id_or_none
from ...webhook.utils import get_webhooks_for_multiple_events
from .. import OrderStatus
from ..actions import (
    WEBHOOK_EVENTS_FOR_ORDER_CREATED,
    _get_extra_for_order_line_logger,
    _get_extra_for_order_logger,
    order_confirmed,
    order_created,
)
from ..fetch import OrderInfo, OrderLineInfo

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


def test_order_created_with_tax_error(order, customer_user, plugins_manager, caplog):
    # given
    order.tax_error = "Empty tax data."
    order.save(update_fields=["tax_error"])

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
    assert "Created non-draft order with tax_error for order" in caplog.text
    assert caplog.records[0].order_id == to_global_id_or_none(order)


@pytest.mark.parametrize(
    "order_field_name",
    [
        "shipping_price_net_amount",
        "shipping_price_gross_amount",
        "total_net_amount",
        "total_gross_amount",
        "subtotal_net_amount",
        "subtotal_gross_amount",
    ],
)
@patch("saleor.order.actions.order_confirmed")
def test_order_created_negative_order_price(
    mock_order_confirmed,
    order_field_name,
    order,
    customer_user,
    plugins_manager,
    caplog,
):
    # given
    setattr(order, order_field_name, -10)
    order.save(update_fields=[order_field_name])
    order_info = OrderInfo(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=None,
        lines_data=[],
    )

    # when
    order_created(order_info, user=customer_user, app=None, manager=plugins_manager)

    # then
    order_extra_data = _get_extra_for_order_logger(order)
    assert order_extra_data.items() <= caplog.records[0].__dict__.items()

    assert "Order with negative prices detected" in caplog.text


@pytest.mark.parametrize(
    "line_field_name",
    [
        "unit_price_net_amount",
        "unit_price_gross_amount",
        "total_price_net_amount",
        "total_price_gross_amount",
    ],
)
@patch("saleor.order.actions.order_confirmed")
def test_order_created_negative_order_line_price(
    mock_order_confirmed,
    line_field_name,
    order_with_lines,
    customer_user,
    plugins_manager,
    caplog,
):
    # given
    order_line = order_with_lines.lines.first()
    setattr(order_line, line_field_name, -10)
    order_line.save(update_fields=[line_field_name])
    order_info = OrderInfo(
        order=order_with_lines,
        customer_email=order_with_lines.get_customer_email(),
        channel=order_with_lines.channel,
        payment=None,
        lines_data=[
            OrderLineInfo(
                line=order_line,
                quantity=order_line.quantity,
            )
        ],
    )

    # when
    order_created(order_info, user=customer_user, app=None, manager=plugins_manager)

    # then
    line_extra_data = _get_extra_for_order_line_logger(order_line)
    assert line_extra_data == caplog.records[0].lines[0]

    assert "Order with negative prices detected" in caplog.text
