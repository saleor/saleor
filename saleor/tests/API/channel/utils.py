from ....graphql.tests.utils import get_graphql_content

CHANNEL_CREATE_MUTATION = """
mutation ChannelCreate($input: ChannelCreateInput!) {
  channelCreate(input: $input) {
    errors {
      field
      message
      code
    }
    channel {
      id
      name
      slug
      currencyCode
      defaultCountry {
        code
      }
      orderSettings {
        automaticallyConfirmAllNewOrders
      }
    }
  }
}
"""


def create_channel(staff_api_client, permissions, warehouses=[]):
    channel_name = "Test channel"
    slug = "test-slug"
    currency = "USD"
    country = "US"
    variables = {
        "input": {
            "name": channel_name,
            "slug": slug,
            "currencyCode": currency,
            "defaultCountry": country,
            "isActive": True,
            "addWarehouses": warehouses,
        }
    }
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION, variables, permissions=permissions
    )
    content = get_graphql_content(response)
    data = content["data"]["channelCreate"]["channel"]
    assert data["name"] == channel_name
    assert data["slug"] == slug
    assert data["currencyCode"] == currency
    assert data["defaultCountry"]["code"] == country
    assert data["orderSettings"]["automaticallyConfirmAllNewOrders"] is True

    return data
