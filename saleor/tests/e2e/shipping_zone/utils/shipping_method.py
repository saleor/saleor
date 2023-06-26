from ...utils import get_graphql_content

SHIPPING_PRICE_CREATE_MUTATION = """
mutation CreateShippingRate($input: ShippingPriceInput!) {
  shippingPriceCreate(input: $input) {
    errors {
      field
      code
      message
    }
    shippingZone {
      id
    }
    shippingMethod {
      id
    }
  }
}
"""


def create_shipping_method(
    staff_api_client,
    shipping_zone_id,
    name="Test shipping method",
    type="PRICE",
):
    variables = {
        "input": {
            "shippingZone": shipping_zone_id,
            "name": name,
            "type": type,
        }
    }

    response = staff_api_client.post_graphql(SHIPPING_PRICE_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["shippingPriceCreate"]["errors"] == []

    data = content["data"]["shippingPriceCreate"]["shippingMethod"]
    assert data["id"] is not None

    return data
