import pytest

from ....order.models import Order
from ...tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_CHECKOUT = """
query getCheckout($token: UUID!) {
    checkout(token: $token) {
        token
    }
}
"""


def test_uuid_scalar_value_passed_as_variable(api_client, checkout):
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_as_variable(api_client, checkout):
    variables = {"token": "wrong-token"}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_uuid_scalar_value_passed_in_input(api_client, checkout):
    token = checkout.token

    query = f"""
        query{{
            checkout(token: "{token}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_in_input(api_client, checkout):
    token = "wrong-token"

    query = f"""
        query{{
            checkout(token: "{token}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


@pytest.mark.parametrize(
    "orders_filter",
    [
        {"created": {"gte": ""}},
        {"created": {"lte": ""}},
        {"created": {"gte": "", "lte": ""}},
    ],
)
def test_order_query_with_filter_created_str_as_date_value(
    orders_filter,
    staff_api_client,
    permission_manage_orders,
    channel_USD,
):
    # given
    query = """
      query ($filter: OrderFilterInput!, ) {
        orders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """

    Order.objects.create(channel=channel_USD)
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content_from_response(response)

    assert 'Variable "$filter" got invalid value' in content["errors"][0]["message"]
