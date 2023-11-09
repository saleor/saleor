from ...utils import get_graphql_content

ORDER_FULFILL_MUTATION = """
mutation orderFulfill ($order: ID!, $input: OrderFulfillInput!) {
  orderFulfill(order: $order, input: $input) {
    order {
      status
      fulfillments {
        id
        status
        created
      }
      id
    }
    fulfillments {
      id
      status
    }
    errors {
      message
      code
      field
    }
  }
}
"""


def order_fulfill(
    staff_api_client,
    id,
    input,
):
    variables = {
        "order": id,
        "input": input,
    }
    response = staff_api_client.post_graphql(
        ORDER_FULFILL_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderFulfill"]

    errors = data["errors"]
    assert errors == []

    return data
