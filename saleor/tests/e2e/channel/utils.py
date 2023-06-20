from ..utils import get_graphql_content

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
      isActive
      orderSettings {
        automaticallyConfirmAllNewOrders
      }
    }
  }
}
"""


def create_channel(
    staff_api_client,
    warehouse_ids=None,
    channel_name="Test channel",
    slug="test-slug",
    currency="USD",
    country="US",
    is_active=True,
):
    if not warehouse_ids:
        warehouse_ids = []

    variables = {
        "input": {
            "name": channel_name,
            "slug": slug,
            "currencyCode": currency,
            "defaultCountry": country,
            "isActive": is_active,
            "addWarehouses": warehouse_ids,
        }
    }

    response = staff_api_client.post_graphql(CHANNEL_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["channelCreate"]["errors"] == []

    data = content["data"]["channelCreate"]["channel"]
    assert data["id"] is not None
    assert data["name"] == channel_name
    assert data["slug"] == slug
    assert data["currencyCode"] == currency
    assert data["defaultCountry"]["code"] == country
    assert data["orderSettings"]["automaticallyConfirmAllNewOrders"] is True
    assert data["isActive"] is is_active

    return data
