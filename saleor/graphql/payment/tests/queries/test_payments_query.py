import json
from decimal import Decimal

import graphene
import pytest

from .....order.models import Order
from .....payment.models import Payment
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import PaymentChargeStatusEnum, TransactionActionEnum


@pytest.fixture
def payments_in_different_channels(
    order_list, payments_dummy, channel_USD, channel_JPY, channel_PLN
):
    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD
    Order.objects.bulk_update(order_list, ["channel"])

    payments_dummy[0].order = order_list[0]
    payments_dummy[1].order = order_list[1]
    payments_dummy[2].order = order_list[2]
    Payment.objects.bulk_update(payments_dummy, ["order"])

    return payments_dummy


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
    payment_txn_captured, permission_group_manage_orders, staff_api_client
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY)

    # then
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


def test_query_payments(
    payment_dummy, permission_group_manage_orders, staff_api_client
):
    # given
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY, {})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    payment_ids = [edge["node"]["id"] for edge in edges]
    assert payment_ids == [payment_id]


def test_query_payments_failed_payment(
    payment_txn_capture_failed, permission_group_manage_orders, staff_api_client
):
    # given
    payment = payment_txn_capture_failed
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY)

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


def test_query_payments_by_user_with_access_to_all_channels(
    payments_in_different_channels,
    permission_group_all_perms_all_channels,
    staff_api_client,
):
    # given
    permission_group_all_perms_all_channels.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY)

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    assert len(edges) == len(payments_in_different_channels)


def test_query_payments_by_user_with_restricted_access_to_channels(
    payments_in_different_channels,
    permission_group_all_perms_channel_USD_only,
    staff_api_client,
    channel_USD,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY)

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    assert len(edges) == 1
    assert edges[0]["node"]["id"] == graphene.Node.to_global_id(
        "Payment", Payment.objects.get(order__channel=channel_USD).pk
    )


def test_query_payments_by_user_with_restricted_access_to_channels_no_acc_channels(
    payments_in_different_channels,
    permission_group_all_perms_without_any_channel,
    staff_api_client,
):
    # given
    permission_group_all_perms_without_any_channel.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY)

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    assert len(edges) == 0


def test_query_payments_by_app(
    payments_in_different_channels, app_api_client, permission_manage_orders
):
    # when
    response = app_api_client.post_graphql(
        PAYMENT_QUERY, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    assert len(edges) == len(payments_in_different_channels)


def test_query_payments_by_customer(payments_in_different_channels, user_api_client):
    # when
    response = user_api_client.post_graphql(PAYMENT_QUERY)

    # then
    assert_no_permission(response)


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
    # given
    query = QUERY_PAYMENT_BY_ID
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"id": payment_id}

    # when
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    payment_data = content["data"]["payment"]
    received_id = payment_data["id"]
    assert received_id == payment_id
    assert not payment_data["checkout"]


def test_query_payment_with_checkout(
    payment_dummy, user_api_client, permission_manage_orders, checkout
):
    # given
    query = QUERY_PAYMENT_BY_ID
    payment = payment_dummy
    payment.order = None
    payment.checkout = checkout
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"id": payment_id}

    # when
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    payment_data = content["data"]["payment"]
    received_id = payment_data["id"]
    assert received_id == payment_id
    assert payment_data["checkout"]["token"] == str(checkout.pk)


def test_staff_query_payment_by_invalid_id(
    staff_api_client, payment_dummy, permission_manage_orders
):
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_BY_ID, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Payment."
    assert content["data"]["payment"] is None


def test_staff_query_payment_with_invalid_object_type(
    staff_api_client, payment_dummy, permission_manage_orders
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", payment_dummy.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_BY_ID, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["payment"] is None
