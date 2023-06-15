import datetime

from .....graphql.tests.utils import get_graphql_content

PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateProductChannelListing(
    $productId: ID!, $input: ProductChannelListingUpdateInput!
) {
  productChannelListingUpdate(id: $productId, input: $input) {
    errors {
      field
      message
      code
    }
    product {
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


def create_product_channel_listing(
    staff_api_client, permissions, product_id, channel_id
):
    publication_date = datetime.date(2007, 1, 1)
    available_for_purchase_date = datetime.date(2007, 1, 1)
    variables = {
        "productId": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": True,
                    "publicationDate": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseDate": available_for_purchase_date,
                }
            ]
        },
    }

    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables,
        permissions=permissions,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    data = content["data"]["productChannelListingUpdate"]["product"]
    assert data["id"] == product_id
    assert data["channelListings"][0]["channel"]["id"] == channel_id

    return data
