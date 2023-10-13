from ...utils import get_graphql_content

ORDER_FULFILLMENT_CANCEL_MUTATION = """
mutation OrderFulfillmentCancel($id: ID!, $input: FulfillmentCancelInput!) {
  orderFulfillmentCancel(id: $id, input: $input) {
    errors {
      message
      field
      code
    }
    order {
      id
      status
      fulfillments {
        id
        status
      }
    }
  }
}
"""


def order_fulfillment_cancel(
    staff_api_client,
    fulfillment_id,
    warehouse_id,
):
    variables = {
        "id": fulfillment_id,
        "input": {"warehouseId": warehouse_id},
    }
    response = staff_api_client.post_graphql(
        ORDER_FULFILLMENT_CANCEL_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderFulfillmentCancel"]

    errors = data["errors"]
    assert errors == []

    return data
