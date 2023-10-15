from saleor.graphql.tests.utils import get_graphql_content

ORDER_MARK_AS_PAID_MUTATION = """
mutation OrderMarkAsPaid($id: ID!, $transactionReference: String) {
  orderMarkAsPaid(id: $id, transactionReference: $transactionReference) {
    order {
        id
        isPaid
        paymentStatus
        paymentStatusDisplay
        status
        statusDisplay
        transactions {
            id
            order {
            id
            }
            name
        }
    }
    errors {
        message
        field
    }
  }
}
"""


def mark_order_paid(
    api_client,
    id,
    transactionReference=None,
):
    variables = {
        "id": id,
        "transactionReference": transactionReference,
    }

    response = api_client.post_graphql(
        ORDER_MARK_AS_PAID_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderMarkAsPaid"]

    errors = data["errors"]

    assert errors == []

    return data
