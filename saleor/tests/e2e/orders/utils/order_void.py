from ...utils import get_graphql_content

ORDER_VOID_MUTATION = """
mutation VoidOrder ($id:ID!){
  orderVoid(id: $id) {
    errors {
      code
      field
      message
    }
    order {
      id
      status
      payments {
        id
      }
      statusDisplay
      events {
        type
      }
    }
  }
}
"""


def raw_order_void(
    staff_api_client,
    order_id,
):
    variables = {
        "id": order_id,
    }
    raw_response = staff_api_client.post_graphql(
        ORDER_VOID_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(raw_response)

    raw_data = content["data"]["orderVoid"]

    return raw_data


def order_void(
    staff_api_client,
    order_id,
):
    response = raw_order_void(
        staff_api_client,
        order_id,
    )

    assert response["errors"] == []

    return response
