import json
from decimal import Decimal

import graphene

from .....payment import PaymentAction
from .....payment.models import Payment
from ....tests.utils import get_graphql_content, get_graphql_content_from_response
from ...enums import PaymentActionEnum, PaymentChargeStatusEnum

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
                actions
                reference
                type
                status
                authorizedAmount{
                        amount
                        currency
                }
                voidedAmount{
                    currency
                    amount
                }
                capturedAmount{
                    currency
                    amount
                }
                refundedAmount{
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
    assert Decimal(amount) == pay.captured_value
    assert data["capturedAmount"]["currency"] == pay.currency
    total = str(data["total"]["amount"])
    assert Decimal(total) == pay.total
    assert data["total"]["currency"] == pay.currency
    assert data["chargeStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    assert data["actions"] == [PaymentActionEnum.REFUND.name]
    txn = pay.transactions.get()
    assert data["transactions"] == [
        {
            "amount": {"currency": pay.currency, "amount": float(str(txn.amount))},
            "error": None,
            "gatewayResponse": "{}",
        }
    ]


def test_payments_from_payment_create_mutation(
    order, permission_manage_orders, staff_api_client
):
    # given
    authorized_value = Decimal("15")
    captured_value = Decimal("3")
    voided_value = Decimal("1")
    refunded_value = Decimal("2")

    Payment.objects.create(
        order_id=order.id,
        status="Authorized card",
        type="Credit card",
        reference="123",
        currency="USD",
        authorized_value=authorized_value,
        captured_value=captured_value,
        voided_value=voided_value,
        refunded_value=refunded_value,
        available_actions=[PaymentAction.CAPTURE, PaymentAction.VOID],
    )

    # when
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["payments"]["edges"][0]["node"]

    # then
    assert data["actions"] == [
        PaymentActionEnum.CAPTURE.name,
        PaymentActionEnum.VOID.name,
    ]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["capturedAmount"]["amount"] == captured_value
    assert data["voidedAmount"]["amount"] == voided_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["reference"] == "123"
    assert data["type"] == "Credit card"
    assert data["status"] == "Authorized card"


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
