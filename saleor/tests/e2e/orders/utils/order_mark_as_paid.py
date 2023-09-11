from saleor.graphql.tests.utils import get_graphql_content

ORDER_MARK_AS_PAID_MUTATION = """
mutation OrderMarkAsPaid($id: ID!) {
  orderMarkAsPaid(id: $id) {
    order {
      isPaid
      paymentStatus
      paymentStatusDisplay
      status
      statusDisplay
    }
    errors{message field}
  }
}
"""


def mark_order_paid(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        ORDER_MARK_AS_PAID_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderMarkAsPaid"]

    errors = data["errors"]

    assert errors == []

    return data
