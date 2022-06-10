from saleor.graphql.core.utils import to_global_id_or_none
from saleor.graphql.tests.utils import get_graphql_content

CHECKOUT_QUERY = """
query getCheckout($token: UUID) {
    checkout(token: $token) {
        id
    }
}
"""


def test_checkout_by_token(checkout, user_api_client, customer_user):
    # given
    checkout.user = customer_user
    checkout.save()
    variables = {"token": checkout.token}

    # when
    response = user_api_client.post_graphql(CHECKOUT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["id"] == to_global_id_or_none(checkout)
