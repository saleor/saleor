from unittest.mock import patch

import graphene

from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....payment import ChargeStatus
from .....plugins.manager import PluginsManager
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import get_graphql_content

ORDER_VOID = """
    mutation voidOrder($id: ID!) {
        orderVoid(id: $id) {
            order {
                paymentStatus
                paymentStatusDisplay
            }
            errors {
                field
                message
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_order_void(
    staff_api_client, permission_manage_orders, payment_txn_preauth, staff_user
):
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]["order"]
    assert data["paymentStatus"] == PaymentChargeStatusEnum.NOT_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    event_payment_voided = order.events.last()
    assert event_payment_voided.type == order_events.OrderEvents.PAYMENT_VOIDED
    assert event_payment_voided.user == staff_user
    order.refresh_from_db()


@patch.object(PluginsManager, "void_payment")
def test_order_void_payment_error(
    mock_void_payment, staff_api_client, permission_manage_orders, payment_txn_preauth
):
    msg = "Oops! Something went wrong."
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    mock_void_payment.side_effect = ValueError(msg)
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderVoid"]["errors"]
    assert errors[0]["field"] == "payment"
    assert errors[0]["message"] == msg

    order_errors = content["data"]["orderVoid"]["errors"]
    assert order_errors[0]["code"] == OrderErrorCode.PAYMENT_ERROR.name

    mock_void_payment.assert_called_once()
