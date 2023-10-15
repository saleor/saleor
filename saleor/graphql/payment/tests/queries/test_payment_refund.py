import graphene

from ....tests.utils import get_graphql_content

QUERY_PAYMENT_REFUND_AMOUNT = """
     query payment($id: ID!) {
        payment(id: $id) {
            id,
            availableRefundAmount{
                amount
            }
            availableCaptureAmount{
                amount
            }
        }
    }
"""


def test_resolve_available_refund_amount_cannot_refund(
    staff_api_client, payment_cancelled, permission_manage_orders
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_REFUND_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_cancelled.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert not content["data"]["payment"]["availableRefundAmount"]


def test_resolve_available_refund_amount(
    staff_api_client, payment_dummy_fully_charged, permission_manage_orders
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_REFUND_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_dummy_fully_charged.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["payment"]["availableRefundAmount"]["amount"] == 98.4
