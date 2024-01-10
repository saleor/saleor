import base64

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
      channelListings {
        maximumOrderPrice {
          amount
        }
        minimumOrderPrice {
          amount
        }
        price {
          amount
        }
        channel {
          id
        }
      }
    }
  }
}
"""


def decode_and_modify_base64_descriptor(encoded_string, new_descriptor=None):
    base64_bytes = encoded_string.encode("ascii")
    decoded_bytes = base64.b64decode(base64_bytes)
    decoded_string = decoded_bytes.decode("ascii")

    modified_string = decoded_string
    if new_descriptor:
        parts = decoded_string.split(":")
        if len(parts) >= 2:
            modified_string = f"{new_descriptor}:{parts[1]}"

    modified_base64 = base64.b64encode(modified_string.encode("ascii")).decode("ascii")

    padding = "=" * ((4 - len(modified_base64) % 4) % 4)
    modified_base64_padded = modified_base64 + padding

    return modified_base64_padded


def create_shipping_method(
    staff_api_client,
    shipping_zone_id,
    name=None,
    type="PRICE",
):
    if name is None:
        name = "Test shipping method"

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

    data["id"] = decode_and_modify_base64_descriptor(data["id"], "ShippingMethod")

    return data
