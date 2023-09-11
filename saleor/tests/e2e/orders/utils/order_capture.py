from saleor.graphql.tests.utils import get_graphql_content

ORDER_CAPTURE_MUTATION = """
mutation OrderCapture($id: ID!, $amount:PositiveDecimal!) {
  orderCapture(id: $id, amount: $amount) {
    errors {
        message
        field
    }
    order {
        id
        status
        paymentStatus
    }
  }
}
"""


def order_capture_payment(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        ORDER_CAPTURE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderCapture"]

    errors = data["errors"]

    assert errors == []

    return data
