from ...utils import get_graphql_content

SHIPPING_PRICE_UPDATE_MUTATION = """
mutation ShippingPriceUpdate($id: ID!, $input: ShippingPriceInput!) {
  shippingPriceUpdate(id: $id, input: $input) {
    errors {
      field
      message
      code
    }
    shippingMethod {
      id
      name
      type
      taxClass {
        id
      }
      channelListings {
        channel {
          id
          slug
        }
        price {
          amount
        }
        maximumOrderPrice {
          amount
        }
        minimumOrderPrice {
          amount
        }
      }
      maximumDeliveryDays
      postalCodeRules {
        id
        start
        end
        inclusionType
      }
      excludedProducts(first: 10) {
        edges {
          node {
            id
          }
        }
      }
    }
  }
}
"""


def update_shipping_price(
    staff_api_client,
    shipping_method_id,
    input,
):
    variables = {
        "id": shipping_method_id,
        "input": input,
    }

    response = staff_api_client.post_graphql(SHIPPING_PRICE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["shippingPriceUpdate"]["errors"] == []

    data = content["data"]["shippingPriceUpdate"]["shippingMethod"]
    assert data["id"] is not None

    return data
