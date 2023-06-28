from ...utils import get_graphql_content

SHIPPING_ZONE_CREATE_MUTATION = """
mutation createShipping($input: ShippingZoneCreateInput!) {
  shippingZoneCreate(input: $input) {
    errors {
      field
      code
      message
    }
    shippingZone {
      id
      name
      description
      warehouses {
        name
      }
      channels {
        id
      }
    }
  }
}
"""


def create_shipping_zone(
    staff_api_client,
    name="Test shipping zone",
    warehouse_ids=None,
    channel_ids=None,
):
    if not warehouse_ids:
        warehouse_ids = []
    if not channel_ids:
        channel_ids = []

    variables = {
        "input": {
            "name": name,
            "countries": "US",
            "addWarehouses": warehouse_ids,
            "addChannels": channel_ids,
        }
    }

    response = staff_api_client.post_graphql(
        SHIPPING_ZONE_CREATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["shippingZoneCreate"]["errors"] == []

    data = content["data"]["shippingZoneCreate"]["shippingZone"]
    assert data["id"] is not None
    assert data["name"] == name

    return data
