from .....graphql.tests.utils import get_graphql_content

PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateProductVariantChannelListing(
    $productVariantId: ID!, $input: [ProductVariantChannelListingAddInput!]!
) {
  productVariantChannelListingUpdate(id: $productVariantId, input: $input) {
    errors {
      field
      message
      code
    }
    variant {
      id
      channelListings {
        id
        channel {
          id
        }
      }
    }
  }
}
"""


def create_product_variant_channel_listing(
    staff_api_client, permissions, product_variant_id, channel_id
):
    variables = {
        "productVariantId": product_variant_id,
        "input": [
            {
                "channelId": channel_id,
                "price": "9.99",
            },
        ],
    }
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables,
        permissions=permissions,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingUpdate"]["variant"]
    assert data["id"] == product_variant_id
    assert data["channelListings"][0]["channel"]["id"] == channel_id

    return data
