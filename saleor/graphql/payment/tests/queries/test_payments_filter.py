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
    payment_dummy, checkouts_list, permission_manage_orders, staff_api_client
):
    # given
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
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    payment_ids = {edge["node"]["id"] for edge in edges}
    assert payment_ids == {
        graphene.Node.to_global_id("Payment", payment.pk)
        for payment in [payment2, payment3]
    }
