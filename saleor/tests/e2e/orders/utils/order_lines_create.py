from saleor.graphql.tests.utils import get_graphql_content

ORDER_LINES_CREATE_MUTATION = """
mutation orderLinesCreate($id: ID!, $input: [OrderLineCreateInput!]!) {
  orderLinesCreate(id: $id, input: $input) {
    order {
      id
      shippingMethods { id }
      lines {
        quantity
        variant {
          id
        }
        totalPrice {
          gross {
            amount
          }
        }
        unitPrice {
          gross {
            amount
          }
        }
        unitDiscountReason
        undiscountedUnitPrice {
          gross {
            amount
          }
        }
      }
    }
    errors {
      field
      message
    }
  }
}
"""


def order_lines_create(
    api_client,
    order_id,
    input,
):
    variables = {"id": order_id, "input": input}

    response = api_client.post_graphql(ORDER_LINES_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    return content["data"]["orderLinesCreate"]
