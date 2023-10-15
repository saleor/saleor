from ...utils import get_graphql_content

PRODUCT_QUERY = """
query Product($id: ID!, $channel: String) {
  product(id: $id, channel: $channel) {
    id
    name
    attributes {
      attribute {
        id
      }
      values {
        name
      }
    }
    pricing {
      onSale
    }
    variants {
      id
      name
      pricing {
        onSale
        discount {
          gross {
            amount
          }
        }
        priceUndiscounted {
          gross {
            amount
          }
        }
        price{
          gross{
            amount
          }
        }
      }
      attributes {
        attribute {
          id
        }
        values {
          name
        }
      }
      channelListings {
        channel {
          id
        }
        price {
          amount
          currency
        }
      }
      stocks {
        warehouse {
          id
        }
        quantity
      }
    }
  }
}
"""


def get_product(
    staff_api_client,
    product_id,
    slug="default-channel",
):
    variables = {
        "id": product_id,
        "channel": slug,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_QUERY,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    data = content["data"]["product"]
    assert data["id"] is not None

    return data
