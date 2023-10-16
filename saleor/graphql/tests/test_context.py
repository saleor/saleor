from unittest import mock

import graphene

from .utils import get_graphql_content

QUERY_ORDER_BY_ID = """
query orderById($id: ID!) {
  order(id: $id) {
    lines {
      totalPrice {
        __typename
      }
    }
  }
}
"""


@mock.patch(
    "saleor.plugins.tests.sample_plugins.SampleAuthorizationPlugin.authenticate_user"
)
def test_user_is_cached_on_request(
    mocked_authenticate_user, api_client, order_with_lines, settings, staff_user
):
    """
    This test case is added to cover edge case when user isn't cached on request
    due to multiple Promises wait inside PluginBackend.authenticate method.
    """
    # given
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.SampleAuthorizationPlugin"]
    mocked_authenticate_user.return_value = staff_user
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {
        "id": order_id,
    }

    # when
    response = api_client.post_graphql(QUERY_ORDER_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["order"]
    assert len(data["lines"]) > 1
    mocked_authenticate_user.assert_called_once()
