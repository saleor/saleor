import graphene

from .....order import FulfillmentStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....payment import ChargeStatus
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
