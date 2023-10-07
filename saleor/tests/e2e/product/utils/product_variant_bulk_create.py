from ...utils import get_graphql_content

PRODUCT_VARIANT_BULK_CREATE_MUTATION = """
mutation ProductVariantBulkCreate($id: ID!, $input: [ProductVariantBulkCreateInput!]!) {
  productVariantBulkCreate(product: $id, variants: $input) {
    errors {
      field
      code
      index
      channels
      message
    }
    productVariants {
      id
      name
      attributes{
        attribute{
          id
        }
        values{
          name
        }
      }
      product{
        id
      }
      channelListings{
        channel{
          id
          slug
        }
        price{
          amount
          currency
        }
      }
      stocks{
        warehouse{
          id
        }
        quantity
      }
    }
  }
}
"""


def create_variants_in_bulk(staff_api_client, product_id, variants_input):
    variables = {
        "id": product_id,
        "input": variants_input,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["productVariantBulkCreate"]["errors"] == []

    data = content["data"]["productVariantBulkCreate"]["productVariants"]
    assert data[0]["id"] is not None

    return data
