from unittest.mock import patch

import graphene

from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....payment import ChargeStatus
from .....plugins.manager import PluginsManager
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import assert_no_permission, get_graphql_content

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
    staff_api_client, permission_group_manage_orders, payment_txn_preauth, staff_user
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(ORDER_VOID, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]["order"]
    assert data["paymentStatus"] == PaymentChargeStatusEnum.NOT_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    event_payment_voided = order.events.last()
    assert event_payment_voided.type == order_events.OrderEvents.PAYMENT_VOIDED
    assert event_payment_voided.user == staff_user
    order.refresh_from_db()


def test_order_void_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    payment_txn_preauth,
    staff_user,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = payment_txn_preauth.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(ORDER_VOID, variables)

    # then
    assert_no_permission(response)


def test_order_void_by_app(
    app_api_client, permission_manage_orders, payment_txn_preauth
):
    # given
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = app_api_client.post_graphql(
        ORDER_VOID, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]["order"]
    assert data["paymentStatus"] == PaymentChargeStatusEnum.NOT_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    event_payment_voided = order.events.last()
    assert event_payment_voided.type == order_events.OrderEvents.PAYMENT_VOIDED
    assert event_payment_voided.user is None
    assert event_payment_voided.app == app_api_client.app


@patch.object(PluginsManager, "void_payment")
def test_order_void_payment_error(
    mock_void_payment,
    staff_api_client,
    permission_group_manage_orders,
    payment_txn_preauth,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    msg = "Oops! Something went wrong."
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    mock_void_payment.side_effect = ValueError(msg)
    response = staff_api_client.post_graphql(ORDER_VOID, variables)
    content = get_graphql_content(response)
    errors = content["data"]["orderVoid"]["errors"]
    assert errors[0]["field"] == "payment"
    assert errors[0]["message"] == msg

    order_errors = content["data"]["orderVoid"]["errors"]
    assert order_errors[0]["code"] == OrderErrorCode.PAYMENT_ERROR.name

    mock_void_payment.assert_called_once()
