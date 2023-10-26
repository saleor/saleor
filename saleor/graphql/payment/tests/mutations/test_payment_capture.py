from unittest.mock import patch

import graphene

from .....payment import TransactionKind
from .....payment.gateways.dummy_credit_card import (
    TOKEN_EXPIRED,
    TOKEN_VALIDATION_MAPPING,
)
from .....payment.models import ChargeStatus
from ....tests.utils import assert_no_permission, get_graphql_content

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


def test_payment_capture_success(
    staff_api_client, permission_group_manage_orders, payment_txn_preauth
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}

    # when
    response = staff_api_client.post_graphql(CAPTURE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE


def test_payment_capture_success_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    payment_txn_preauth,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order = payment_txn_preauth.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}

    # when
    response = staff_api_client.post_graphql(CAPTURE_QUERY, variables)

    # then
    assert_no_permission(response)


def test_payment_capture_success_by_app(
    app_api_client, permission_manage_orders, payment_txn_preauth
):
    # given
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}

    # when
    response = app_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE


def test_payment_capture_with_invalid_argument(
    staff_api_client, permission_group_manage_orders, payment_txn_preauth
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}

    # when
    response = staff_api_client.post_graphql(CAPTURE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."


def test_payment_capture_with_unauthorized_payment(
    staff_api_client, permission_group_manage_orders, payment_dummy
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment = payment_dummy
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 1}

    # when
    response = staff_api_client.post_graphql(CAPTURE_QUERY, variables)

    # then
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
    staff_api_client, permission_group_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment = payment_txn_preauth

    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)

    # when
    response = staff_api_client.post_graphql(CAPTURE_QUERY, variables)

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
    staff_api_client, permission_group_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(CAPTURE_QUERY, variables)

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
