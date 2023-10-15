from ...utils import get_graphql_content

VOUCHER_CREATE_CHANNEL_LISTING_MUTATION = """
mutation VoucherChannelListingUpdate($id: ID!, $input: VoucherChannelListingInput!) {
  voucherChannelListingUpdate(id: $id, input: $input) {
    errors {
      field
      message
      code
    }
    voucher {
      id
      startDate
      discountValueType
      type
      channelListings {
        id
        channel {
          id
        }
        discountValue
        currency
        minSpent {
          amount
        }
      }
    }
  }
}
"""


def create_voucher_channel_listing(
    staff_api_client,
    voucher_id,
    addChannels=None,
    removeChannels=None,
):
    if not addChannels:
        addChannels = []

    if not removeChannels:
        removeChannels = []

    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": addChannels,
            "removeChannels": removeChannels,
        },
    }

    response = staff_api_client.post_graphql(
        VOUCHER_CREATE_CHANNEL_LISTING_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["voucherChannelListingUpdate"]["errors"] == []

    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    return data
