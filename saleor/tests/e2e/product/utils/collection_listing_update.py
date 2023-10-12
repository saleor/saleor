from ...utils import get_graphql_content

COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation CollectionListing($id: ID!, $input: CollectionChannelListingUpdateInput!) {
  collectionChannelListingUpdate(id: $id, input: $input) {
    errors {
      code
      field
      message
      channels
    }
    collection {
      id
      channelListings {
        id
        isPublished
        publishedAt
        channel {
          id
        }
      }
    }
  }
}
"""


def create_collection_channel_listing(
    staff_api_client,
    collection_id,
    channel_id,
    publication_date=None,
    is_published=False,
):
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": is_published,
                    "publicationDate": publication_date,
                }
            ],
            "removeChannels": [],
        },
    }

    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    data = content["data"]["collectionChannelListingUpdate"]["collection"]
    assert content["data"]["collectionChannelListingUpdate"]["errors"] == []
    assert data["channelListings"][0]["channel"]["id"] == channel_id

    return data
