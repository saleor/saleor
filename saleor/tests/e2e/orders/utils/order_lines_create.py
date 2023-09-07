from saleor.graphql.tests.utils import get_graphql_content

ORDER_LINES_CREATE_MUTATION = """
mutation orderLinesCreate($id: ID!, $input: [OrderLineCreateInput!]! ){
  orderLinesCreate(id: $id input: $input, ) {
    order {
      lines {
        quantity
        variant {
          id
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
