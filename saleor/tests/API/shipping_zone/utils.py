from ....graphql.tests.utils import get_graphql_content

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


def create_shipping_zone(staff_api_client, permissions, warehouse_ids, channel_ids):
    name = "Test shipping zone"
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
        permissions=permissions,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]["shippingZone"]
    assert data["name"] == name

    return data
