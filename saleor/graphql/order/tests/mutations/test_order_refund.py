from decimal import Decimal
from unittest.mock import patch

import graphene

from .....order import FulfillmentStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....payment import ChargeStatus
from .....tests.utils import flush_post_commit_hooks
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_REFUND_MUTATION = """
    mutation refundOrder($id: ID!, $amount: PositiveDecimal!) {
        orderRefund(id: $id, amount: $amount) {
            order {
                paymentStatus
                paymentStatusDisplay
                isPaid
                status
            }
            errors {
                code
                field
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_order_refund(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    staff_api_client,
    permission_group_manage_orders,
    payment_txn_captured,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = payment_txn_captured.order
    query = ORDER_REFUND_MUTATION
    amount = Decimal(10)
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "amount": amount}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.PARTIALLY_REFUNDED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(
        ChargeStatus.PARTIALLY_REFUNDED
    )
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"] is False

    refund_order_event = order.events.filter(
        type=order_events.OrderEvents.PAYMENT_REFUNDED
    ).first()
    assert refund_order_event.parameters["amount"] == str(amount)

    refunded_fulfillment = order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED
    ).first()
    assert refunded_fulfillment
    assert refunded_fulfillment.total_refund_amount == amount
    assert refunded_fulfillment.shipping_refund_amount is None

    flush_post_commit_hooks()
    mock_order_updated.assert_called_once_with(order)
    mock_order_refunded.assert_called_once_with(order)
    assert amount < order.total.gross.amount
    assert not mock_order_fully_refunded.called


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_order_fully_refunded(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    staff_api_client,
    permission_group_manage_orders,
    payment_txn_captured,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = payment_txn_captured.order
    payment_txn_captured.total = order.total.gross.amount
    payment_txn_captured.captured_amount = payment_txn_captured.total
    payment_txn_captured.save()

    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_captured.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_REFUNDED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_REFUNDED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"] is False

    refund_order_event = order.events.filter(
        type=order_events.OrderEvents.PAYMENT_REFUNDED
    ).first()
    assert refund_order_event.parameters["amount"] == str(amount)

    refunded_fulfillment = order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED
    ).first()
    assert refunded_fulfillment
    assert refunded_fulfillment.total_refund_amount == payment_txn_captured.total
    assert refunded_fulfillment.shipping_refund_amount is None

    flush_post_commit_hooks()
    mock_order_updated.assert_called_once_with(order)
    mock_order_refunded.assert_called_once_with(order)
    mock_order_fully_refunded.assert_called_once_with(order)


def test_order_refund_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    payment_txn_captured,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = payment_txn_captured.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_captured.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_order_refund_by_app(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    app_api_client,
    permission_manage_orders,
    payment_txn_captured,
):
    # given
    order = payment_txn_captured.order
    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_captured.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_REFUNDED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_REFUNDED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"] is False

    refund_order_event = order.events.filter(
        type=order_events.OrderEvents.PAYMENT_REFUNDED
    ).first()
    assert refund_order_event.parameters["amount"] == str(amount)

    refunded_fulfillment = order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED
    ).first()
    assert refunded_fulfillment
    assert refunded_fulfillment.total_refund_amount == payment_txn_captured.total
    assert refunded_fulfillment.shipping_refund_amount is None

    flush_post_commit_hooks()
    mock_order_updated.assert_called_once_with(order)
    mock_order_refunded.assert_called_once_with(order)
    mock_order_fully_refunded.assert_called_once_with(order)


def test_order_refund_with_gift_card_lines(
    staff_api_client, permission_group_manage_orders, gift_card_shippable_order_line
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = gift_card_shippable_order_line.order
    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id, "amount": 10.0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]
    assert not data["order"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert data["errors"][0]["field"] == "id"
