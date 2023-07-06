import datetime

import pytz

from ...utils import get_graphql_content

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
        isPublished
        publicationDate
        visibleInListings
        isAvailableForPurchase
        availableForPurchaseAt
        channel {
          id
        }
      }
    }
  }
}
"""


def create_product_channel_listing(
    staff_api_client,
    product_id,
    channel_id,
    publication_date=datetime.date(2007, 1, 1),
    is_published=True,
    visible_in_listings=True,
    available_for_purchase_datetime=datetime.datetime(2007, 1, 1, tzinfo=pytz.utc),
    is_available_for_purchase=True,
):
    variables = {
        "productId": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": is_published,
                    "publicationDate": publication_date,
                    "visibleInListings": visible_in_listings,
                    "isAvailableForPurchase": is_available_for_purchase,
                    "availableForPurchaseAt": available_for_purchase_datetime,
                }
            ]
        },
    }

    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["productChannelListingUpdate"]["errors"] == []

    data = content["data"]["productChannelListingUpdate"]["product"]
    assert data["id"] == product_id
    channel_listing_data = data["channelListings"][0]
    assert channel_listing_data["channel"]["id"] == channel_id
    assert channel_listing_data["isPublished"] is is_published
    assert channel_listing_data["publicationDate"] == publication_date.isoformat()
    assert channel_listing_data["visibleInListings"] is visible_in_listings
    assert channel_listing_data["isAvailableForPurchase"] is is_available_for_purchase
    assert (
        channel_listing_data["availableForPurchaseAt"]
        == available_for_purchase_datetime.isoformat()
    )

    return data
