from ...utils import get_graphql_content

ORDER_FULFILLMENT_UPDATE_TRACKING = """
mutation OrderFulfillmentUpdateTracking(
  $id: ID!
  $input: FulfillmentUpdateTrackingInput!
) {
  orderFulfillmentUpdateTracking(id: $id, input: $input) {
    errors {
      message
      code
      field
    }
    order {
      id
      status
      fulfillments {
        id
        status
        trackingNumber
      }
    }
  }
}
"""


def order_add_tracking(
    staff_api_client,
    fulfillment_id,
    tracking_number,
):
    variables = {
        "id": fulfillment_id,
        "input": {
            "trackingNumber": tracking_number,
            "notifyCustomer": True,
        },
    }

    response = staff_api_client.post_graphql(
        ORDER_FULFILLMENT_UPDATE_TRACKING, variables
    )
    content = get_graphql_content(response)

    assert content["data"]["orderFulfillmentUpdateTracking"]["errors"] == []

    data = content["data"]["orderFulfillmentUpdateTracking"]["order"]

    return data
