import pytest

from ....tests.utils import get_graphql_content

SHIPPING_METHODS_QUERY = """
query GetShippingMethods($channel: String) {
  shippingZones(first: 10, channel: $channel) {
    edges {
      node {
        shippingMethods {
          id
          name
          minimumOrderWeight {
            unit
            value
          }
          maximumOrderWeight {
            unit
            value
          }
          type
          channelListings {
            id
            channel {
              id
              name
            }
          }
          price {
            amount
            currency
          }
          maximumOrderPrice {
            currency
            amount
          }
          minimumOrderPrice {
            currency
            amount
          }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_vouchers_query_with_channel_slug(
    staff_api_client,
    shipping_zones,
    channel_USD,
    permission_manage_shipping,
    count_queries,
):
    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            SHIPPING_METHODS_QUERY,
            variables,
            permissions=[permission_manage_shipping],
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_vouchers_query_without_channel_slug(
    staff_api_client, shipping_zones, permission_manage_shipping, count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            SHIPPING_METHODS_QUERY,
            {},
            permissions=[permission_manage_shipping],
            check_no_permissions=False,
        )
    )
