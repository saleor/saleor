import json
from decimal import Decimal

import graphene

from ....tests.utils import get_graphql_content, get_graphql_content_from_response
from ...enums import PaymentChargeStatusEnum, TransactionActionEnum

PAYMENT_QUERY = """ query Payments($filter: PaymentFilterInput){
    payments(first: 20, filter: $filter) {
        edges {
            node {
                id
                gateway
                total {
                    amount
                    currency
                }
                actions
                chargeStatus
                transactions {
                    error
                    gatewayResponse
                    amount {
                        currency
                        amount
                    }
                }
                capturedAmount{
                    currency
                    amount
                }
            }
        }
    }
}
"""


def test_payments_query(
    payment_txn_captured, permission_manage_orders, staff_api_client
):
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["payments"]["edges"][0]["node"]
    pay = payment_txn_captured
    assert data["gateway"] == pay.gateway
    amount = str(data["capturedAmount"]["amount"])
    assert Decimal(amount) == pay.captured_amount
    assert data["capturedAmount"]["currency"] == pay.currency
    total = str(data["total"]["amount"])
    assert Decimal(total) == pay.total
    assert data["total"]["currency"] == pay.currency
    assert data["chargeStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    assert data["actions"] == [TransactionActionEnum.REFUND.name]
    txn = pay.transactions.get()
    assert data["transactions"] == [
        {
            "amount": {"currency": pay.currency, "amount": float(str(txn.amount))},
            "error": None,
            "gatewayResponse": "{}",
        }
    ]


def test_query_payments(payment_dummy, permission_manage_orders, staff_api_client):
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, {}, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    payment_ids = [edge["node"]["id"] for edge in edges]
    assert payment_ids == [payment_id]


def test_query_payments_failed_payment(
    payment_txn_capture_failed, permission_manage_orders, staff_api_client
):
    # given
    payment = payment_txn_capture_failed

    # when
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["payments"]["edges"][0]["node"]

    assert data["gateway"] == payment.gateway
    amount = str(data["capturedAmount"]["amount"])
    assert Decimal(amount) == payment.captured_amount
    assert data["capturedAmount"]["currency"] == payment.currency
    total = str(data["total"]["amount"])
    assert Decimal(total) == payment.total
    assert data["total"]["currency"] == payment.currency
    assert data["chargeStatus"] == PaymentChargeStatusEnum.REFUSED.name
    assert data["actions"] == []
    txn = payment.transactions.get()
    assert data["transactions"] == [
        {
            "amount": {"currency": payment.currency, "amount": float(str(txn.amount))},
            "error": txn.error,
            "gatewayResponse": json.dumps(txn.gateway_response),
        }
    ]


QUERY_PAYMENT_BY_ID = """
    query payment($id: ID!) {
        payment(id: $id) {
            id
            checkout {
                token
            }
        }
    }
"""


def test_query_payment(payment_dummy, user_api_client, permission_manage_orders):
    query = QUERY_PAYMENT_BY_ID
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"id": payment_id}
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    payment_data = content["data"]["payment"]
    received_id = payment_data["id"]
    assert received_id == payment_id
    assert not payment_data["checkout"]


def test_query_payment_with_checkout(
    payment_dummy, user_api_client, permission_manage_orders, checkout
):
    query = QUERY_PAYMENT_BY_ID
    payment = payment_dummy
    payment.order = None
    payment.checkout = checkout
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"id": payment_id}
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    payment_data = content["data"]["payment"]
    received_id = payment_data["id"]
    assert received_id == payment_id
    assert payment_data["checkout"]["token"] == str(checkout.pk)


def test_staff_query_payment_by_invalid_id(
    staff_api_client, payment_dummy, permission_manage_orders
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_BY_ID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["payment"] is None


def test_staff_query_payment_with_invalid_object_type(
    staff_api_client, payment_dummy, permission_manage_orders
):
    variables = {"id": graphene.Node.to_global_id("Order", payment_dummy.pk)}
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_BY_ID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert content["data"]["payment"] is None
