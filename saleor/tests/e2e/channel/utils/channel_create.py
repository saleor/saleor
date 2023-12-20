import uuid

from ...utils import get_graphql_content

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
      warehouses {
        id
        slug
        shippingZones(first: 10) {
          edges {
            node {
              id
            }
          }
        }
      }
      stockSettings {
        allocationStrategy
      }
      isActive
      orderSettings {
        markAsPaidStrategy
        automaticallyConfirmAllNewOrders
        allowUnpaidOrders
        automaticallyConfirmAllNewOrders
        expireOrdersAfter
        deleteExpiredOrdersAfter
      }
    }
  }
}
"""


def create_channel(
    staff_api_client,
    warehouse_ids=None,
    channel_name="Test channel",
    slug=None,
    currency="USD",
    country="US",
    shipping_zones=None,
    is_active=True,
    order_settings={},
):
    if not warehouse_ids:
        warehouse_ids = []

    if slug is None:
        slug = f"channel_slug_{uuid.uuid4()}"

    variables = {
        "input": {
            "name": channel_name,
            "slug": slug,
            "currencyCode": currency,
            "defaultCountry": country,
            "isActive": is_active,
            "addWarehouses": warehouse_ids,
            "addShippingZones": shipping_zones,
            "orderSettings": {
                "markAsPaidStrategy": "PAYMENT_FLOW",
                "automaticallyFulfillNonShippableGiftCard": False,
                "allowUnpaidOrders": False,
                "automaticallyConfirmAllNewOrders": True,
                "expireOrdersAfter": 60,
                "deleteExpiredOrdersAfter": 1,
                **order_settings,
            },
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
