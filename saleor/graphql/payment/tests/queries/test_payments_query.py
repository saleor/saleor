import json
from decimal import Decimal

import graphene

from ....tests.utils import get_graphql_content
from ...enums import OrderAction, PaymentChargeStatusEnum

PAYMENT_QUERY = """ query Payments($filter: PaymentFilterInput){
    payments(first: 20, filter: $filter) {
        edges {
            node {
                id
                gateway
                capturedAmount {
                    amount
                    currency
                }
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
    assert data["actions"] == [OrderAction.REFUND.name]
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
