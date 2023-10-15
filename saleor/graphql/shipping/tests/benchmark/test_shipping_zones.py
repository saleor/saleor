import pytest

from ....tests.utils import get_graphql_content

SHIPPING_ZONES_QUERY = """
query GetShippingZones($channel: String) {
  shippingZones(first: 100, channel: $channel) {
    edges {
      node {
        warehouses {
            id
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_shipping_zones_query(
    staff_api_client,
    shipping_zones_with_warehouses,
    channel_USD,
    permission_manage_shipping,
    count_queries,
):
    variables = {"channel": channel_USD.slug}
    response = get_graphql_content(
        staff_api_client.post_graphql(
            SHIPPING_ZONES_QUERY,
            variables,
            permissions=[permission_manage_shipping],
            check_no_permissions=False,
        )
    )
    data = response["data"]["shippingZones"]["edges"]
    assert len(data) == 10
    for zone in data:
        assert len(zone["node"]["warehouses"]) == 2
