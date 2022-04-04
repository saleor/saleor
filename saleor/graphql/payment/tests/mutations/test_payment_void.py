from decimal import Decimal

import graphene
from mock import patch

from .....order import OrderEvents
from .....payment import ChargeStatus, PaymentAction, TransactionKind
from .....payment.interface import PaymentActionData
from .....payment.models import Payment
from ....core.enums import PaymentErrorCode
from ....tests.utils import get_graphql_content

VOID_QUERY = """
    mutation PaymentVoid($paymentId: ID!) {
        paymentVoid(paymentId: $paymentId) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.payment_action_request")
def test_payment_void_with_payment_action_request(
    mocked_payment_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    payment = Payment.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )

    mocked_is_active.return_value = True
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.VOID,
            action_value=None,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.PAYMENT_VOID_REQUESTED
    assert event.parameters["payment_id"] == payment.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.payment_action_request")
def test_payment_void_with_payment_action_request_for_checkout(
    mocked_payment_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    checkout,
):
    # given
    payment = Payment.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal("10"),
    )

    mocked_is_active.return_value = True
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {
        "paymentId": payment_id,
    }

    # when
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.VOID,
            action_value=None,
        ),
        channel_slug=checkout.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_payment_void_with_payment_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    payment = Payment.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10.0"),
    )
    mocked_is_active.return_value = False
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    assert data["errors"][0]["code"] == (
        PaymentErrorCode.MISSING_PAYMENT_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called


def test_payment_void_success(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.is_active is False
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID


def test_payment_void_gateway_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert data["errors"]
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["message"] == "Unable to void the transaction."
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    assert payment_txn_preauth.is_active is True
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID
    assert not txn.is_success
