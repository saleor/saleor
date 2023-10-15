from saleor.graphql.tests.utils import get_graphql_content

DRAFT_ORDER_DELETE_MUTATION = """
mutation DraftOrderDelete($id: ID!) {
  draftOrderDelete(id: $id) {
    errors {
		message
        field
    }
    order {
		status
    }
  }
}
"""


def draft_order_delete(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        DRAFT_ORDER_DELETE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["draftOrderDelete"]
    errors = data["errors"]

    assert errors == []

    return data
