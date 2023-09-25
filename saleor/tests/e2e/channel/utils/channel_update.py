from ...utils import get_graphql_content

CHANNEL_UPDATE_MUTATION = """
mutation ChannelUpdate($id: ID!, $input: ChannelUpdateInput!) {
  channelUpdate(id: $id, input: $input) {
    channel {
      id
      orderSettings {
        deleteExpiredOrdersAfter
        allowUnpaidOrders
        automaticallyFulfillNonShippableGiftCard
        automaticallyConfirmAllNewOrders
        expireOrdersAfter
        deleteExpiredOrdersAfter
      }
    }
    errors {
      message
      field
    }
  }
}

"""


def update_channel(staff_api_client, id, input):
    variables = {
        "id": id,
        "input": input,
    }

    response = staff_api_client.post_graphql(CHANNEL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["channelUpdate"]["errors"] == []

    data = content["data"]["channelUpdate"]["channel"]
    assert data["id"] is not None

    return data
