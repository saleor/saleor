from decimal import Decimal
from unittest.mock import patch

import graphene

from .....order import FulfillmentStatus, OrderEvents
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....payment import ChargeStatus, TransactionAction
from .....payment.interface import TransactionActionData
from .....payment.models import TransactionItem
from ....core.utils import to_global_id_or_none
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import get_graphql_content

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


def test_order_refund(staff_api_client, permission_manage_orders, payment_txn_captured):
    order = payment_txn_captured.order
    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_captured.total)
    variables = {"id": order_id, "amount": amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
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


def test_order_refund_with_gift_card_lines(
    staff_api_client, permission_manage_orders, gift_card_shippable_order_line
):
    order = gift_card_shippable_order_line.order
    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id, "amount": 10.0}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]
    assert not data["order"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert data["errors"][0]["field"] == "id"


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_action_request")
def test_order_refund_with_transaction_action_request(
    mocked_transaction_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    transaction = TransactionItem.objects.create(
        status="Captured",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )
    refund_value = Decimal(5.0)
    mocked_is_active.return_value = True

    order_id = to_global_id_or_none(order)
    variables = {"id": order_id, "amount": refund_value}

    # when
    response = staff_api_client.post_graphql(
        ORDER_REFUND_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_transaction_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=refund_value,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == refund_value
    assert event.parameters["reference"] == transaction.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_order_refund_with_transaction_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    authorized_value = Decimal("10")
    TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorized_value,
    )
    mocked_is_active.return_value = False

    order_id = to_global_id_or_none(order)
    variables = {"id": order_id, "amount": authorized_value}

    # when
    response = staff_api_client.post_graphql(
        ORDER_REFUND_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == (
        OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called
