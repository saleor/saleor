from decimal import Decimal
from unittest.mock import patch

import graphene

from .....order import OrderEvents
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....payment import ChargeStatus, TransactionAction
from .....payment.interface import TransactionActionData
from .....payment.models import TransactionItem
from .....plugins.manager import PluginsManager
from ....core.utils import to_global_id_or_none
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


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_action_request")
def test_order_void_with_transaction_action_request(
    mocked_transaction_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    transaction = TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )

    mocked_is_active.return_value = True

    order_id = to_global_id_or_none(order)

    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_transaction_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.VOID,
            action_value=None,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_VOID_REQUESTED
    assert event.parameters["reference"] == transaction.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_order_void_with_transaction_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10.0"),
    )
    mocked_is_active.return_value = False

    order_id = to_global_id_or_none(order)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    assert data["errors"][0]["code"] == (
        OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called
