import graphene

from ....tests.utils import get_graphql_content

QUERY_PAYMENT_CAPTURE_AMOUNT = """
     query payment($id: ID!) {
        payment(id: $id) {
            id,
            availableCaptureAmount{
                amount
            }
        }
    }
"""


def test_resolve_available_capture_amount_cannot_capture(
    staff_api_client, payment_cancelled, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_CAPTURE_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_cancelled.pk)},
    )
    content = get_graphql_content(response)

    assert not content["data"]["payment"]["availableCaptureAmount"]


def test_resolve_available_capture_amount(
    staff_api_client, payment_dummy, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_CAPTURE_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_dummy.pk)},
    )
    content = get_graphql_content(response)

    assert content["data"]["payment"]["availableCaptureAmount"]["amount"] == 98.4
