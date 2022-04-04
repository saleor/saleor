from decimal import Decimal

import graphene
from mock import patch

from saleor.graphql.core.enums import PaymentErrorCode
from saleor.graphql.tests.utils import get_graphql_content
from saleor.order import OrderEvents
from saleor.payment import PaymentAction, TransactionKind
from saleor.payment.interface import PaymentActionData
from saleor.payment.models import ChargeStatus, Payment

REFUND_QUERY = """
    mutation PaymentRefund($paymentId: ID!, $amount: PositiveDecimal) {
        paymentRefund(paymentId: $paymentId, amount: $amount) {
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
def test_payment_refund_with_payment_action_request(
    mocked_payment_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    payment = Payment.objects.create(
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
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": refund_value}

    # when
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.REFUND,
            action_value=refund_value,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.PAYMENT_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == refund_value
    assert event.parameters["payment_id"] == payment.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.payment_action_request")
def test_payment_refund_with_payment_action_request_for_checkout(
    mocked_payment_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    checkout,
):
    # given
    payment = Payment.objects.create(
        status="Captured",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal("10"),
    )
    refund_value = Decimal(5.0)
    mocked_is_active.return_value = True
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": refund_value}

    # when
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.REFUND,
            action_value=refund_value,
        ),
        channel_slug=checkout.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.payment_action_request")
def test_payment_refund_with_payment_action_request_without_amount(
    mocked_payment_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    captured_value = Decimal("10")
    payment = Payment.objects.create(
        status="Captured",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        captured_value=captured_value,
    )
    mocked_is_active.return_value = True
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.REFUND,
            action_value=captured_value,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.PAYMENT_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == captured_value
    assert event.parameters["payment_id"] == payment.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_payment_capture_with_payment_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    captured_value = Decimal("10")
    payment = Payment.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        authorized_value=captured_value,
    )
    mocked_is_active.return_value = False
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    assert data["errors"][0]["code"] == (
        PaymentErrorCode.MISSING_PAYMENT_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called


def test_payment_refund_success(
    staff_api_client, permission_manage_orders, payment_txn_captured
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert not data["errors"]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND


def test_payment_refund_with_invalid_argument(
    staff_api_client, permission_manage_orders, payment_txn_captured
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."


def test_payment_refund_error(
    staff_api_client, permission_manage_orders, payment_txn_captured, monkeypatch
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]

    assert data["errors"] == [
        {
            "field": None,
            "message": "Unable to process refund",
            "code": PaymentErrorCode.PAYMENT_ERROR.name,
        }
    ]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success
