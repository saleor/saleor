from saleor.graphql.tests.utils import get_graphql_content

DRAFT_ORDER_BULK_DELETE_MUTATION = """
mutation DraftBulkDelete($ids: [ID!]!) {
  draftOrderBulkDelete(ids: $ids) {
    errors {
      field
      code
      message
    }
    count
  }
}
"""


def draft_order_bulk_delete(api_client, ids_list):
    variables = {"ids": ids_list}

    response = api_client.post_graphql(
        DRAFT_ORDER_BULK_DELETE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["draftOrderBulkDelete"]

    return data
