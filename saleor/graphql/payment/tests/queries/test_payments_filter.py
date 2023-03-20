import graphene

from .....payment.models import Payment
from ....tests.utils import get_graphql_content

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


def test_query_payments_filter_by_checkout(
    payment_dummy, checkouts_list, permission_group_manage_orders, staff_api_client
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment1 = payment_dummy
    payment1.checkout = checkouts_list[0]
    payment1.save()

    payment2 = Payment.objects.get(id=payment1.id)
    payment2.id = None
    payment2.checkout = checkouts_list[1]
    payment2.save()

    payment3 = Payment.objects.get(id=payment1.id)
    payment3.id = None
    payment3.checkout = checkouts_list[2]
    payment3.save()

    variables = {
        "filter": {
            "checkouts": [
                graphene.Node.to_global_id("Checkout", checkout.pk)
                for checkout in checkouts_list[1:4]
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    payment_ids = {edge["node"]["id"] for edge in edges}
    assert payment_ids == {
        graphene.Node.to_global_id("Payment", payment.pk)
        for payment in [payment2, payment3]
    }


def test_query_payments_filter_by_one_id(
    payments_dummy, permission_group_manage_orders, staff_api_client
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    search_payment = payments_dummy[0]

    variables = {
        "filter": {
            "ids": [graphene.Node.to_global_id("Payment", search_payment.pk)],
        }
    }

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    result_payments = content["data"]["payments"]["edges"]

    assert len(result_payments) == 1
    _, id = graphene.Node.from_global_id(result_payments[0]["node"]["id"])
    assert id == str(search_payment.pk)


def test_query_payments_filter_by_multiple_ids(
    payments_dummy, permission_group_manage_orders, staff_api_client
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    search_payments = payments_dummy[:2]
    search_payments_ids = [
        graphene.Node.to_global_id("Payment", payment.pk) for payment in search_payments
    ]

    variables = {"filter": {"ids": search_payments_ids}}

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    expected_ids = [str(payment.pk) for payment in search_payments]

    result_payments = content["data"]["payments"]["edges"]

    assert len(result_payments) == len(search_payments)
    for result_payment in result_payments:
        _, id = graphene.Node.from_global_id(result_payment["node"]["id"])
        assert id in expected_ids


def test_query_payments_filter_by_empty_id_list(
    payments_dummy, permission_group_manage_orders, staff_api_client
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"filter": {"ids": []}}

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    expected_ids = [str(payment.pk) for payment in payments_dummy]

    result_payments = content["data"]["payments"]["edges"]

    assert len(result_payments) == len(payments_dummy)
    for result_payment in result_payments:
        _, id = graphene.Node.from_global_id(result_payment["node"]["id"])
        assert id in expected_ids


def test_query_payments_filter_by_not_existing_id(
    payments_dummy, permission_group_manage_orders, staff_api_client
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    search_pk = max([payment.pk for payment in payments_dummy]) + 1
    search_id = graphene.Node.to_global_id("Payment", search_pk)
    variables = {"filter": {"ids": [search_id]}}

    # when
    response = staff_api_client.post_graphql(PAYMENT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    result_payments = content["data"]["payments"]["edges"]

    assert len(result_payments) == 0
