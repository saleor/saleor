from saleor.graphql.tests.utils import get_graphql_content

ORDER_CANCEL_MUTATION = """
mutation OrderCancel($id: ID!) {
  orderCancel(id: $id) {
    errors {
        message
        field
    }
    order {
        id
        status
        paymentStatus
        isPaid
        totalBalance { amount }
        total {
            gross {
                amount
            }
        }
    }
  }
}
"""


def order_cancel(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        ORDER_CANCEL_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderCancel"]

    errors = data["errors"]

    assert errors == []

    return data
