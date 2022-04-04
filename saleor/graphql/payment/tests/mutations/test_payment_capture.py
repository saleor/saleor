from decimal import Decimal
from unittest.mock import patch

import graphene

from .....order import OrderEvents
from .....payment import PaymentAction, TransactionKind
from .....payment.gateways.dummy_credit_card import (
    TOKEN_EXPIRED,
    TOKEN_VALIDATION_MAPPING,
)
from .....payment.interface import PaymentActionData
from .....payment.models import ChargeStatus, Payment
from ....core.enums import PaymentErrorCode
from ....tests.utils import get_graphql_content

CAPTURE_QUERY = """
    mutation PaymentCapture($paymentId: ID!, $amount: PositiveDecimal) {
        paymentCapture(paymentId: $paymentId, amount: $amount) {
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
def test_payment_capture_with_payment_action_request(
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
    capture_value = Decimal(5.0)
    mocked_is_active.return_value = True
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": capture_value}

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.CAPTURE,
            action_value=capture_value,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.PAYMENT_CAPTURE_REQUESTED
    assert Decimal(event.parameters["amount"]) == capture_value
    assert event.parameters["payment_id"] == payment.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.payment_action_request")
def test_payment_capture_with_payment_action_request_for_checkout(
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
    capture_value = Decimal(5.0)
    mocked_is_active.return_value = True
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": capture_value}

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.CAPTURE,
            action_value=capture_value,
        ),
        channel_slug=checkout.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.payment_action_request")
def test_payment_capture_with_payment_action_request_without_amount(
    mocked_payment_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    authorization_value = Decimal("10")
    payment = Payment.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorization_value,
    )
    mocked_is_active.return_value = True
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        PaymentActionData(
            payment=payment,
            action_requested=PaymentAction.CAPTURE,
            action_value=authorization_value,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.PAYMENT_CAPTURE_REQUESTED
    assert Decimal(event.parameters["amount"]) == authorization_value
    assert event.parameters["payment_id"] == payment.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_payment_capture_with_payment_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    authorization_value = Decimal("10")
    payment = Payment.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorization_value,
    )
    mocked_is_active.return_value = False
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    assert data["errors"][0]["code"] == (
        PaymentErrorCode.MISSING_PAYMENT_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called


def test_payment_capture_success(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE


def test_payment_capture_with_invalid_argument(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."


def test_payment_capture_with_payment_non_authorized_yet(
    staff_api_client, permission_manage_orders, payment_dummy
):
    """Ensure capture a payment that is set as authorized is failing with
    the proper error message.
    """
    payment = payment_dummy
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 1}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [
        {
            "field": None,
            "message": "Cannot find successful auth transaction.",
            "code": "PAYMENT_ERROR",
        }
    ]


def test_payment_capture_gateway_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    payment = payment_txn_preauth

    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [
        {"field": None, "message": "Unable to process capture", "code": "PAYMENT_ERROR"}
    ]

    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.is_success


@patch(
    "saleor.payment.gateways.dummy_credit_card.plugin."
    "DummyCreditCardGatewayPlugin.DEFAULT_ACTIVE",
    True,
)
def test_payment_capture_gateway_dummy_credit_card_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    token = TOKEN_EXPIRED
    error = TOKEN_VALIDATION_MAPPING[token]

    payment = payment_txn_preauth
    payment.gateway = "mirumee.payments.dummy_credit_card"
    payment.save()

    transaction = payment.transactions.last()
    transaction.token = token
    transaction.save()

    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [
        {"field": None, "message": error, "code": "PAYMENT_ERROR"}
    ]

    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.is_success
