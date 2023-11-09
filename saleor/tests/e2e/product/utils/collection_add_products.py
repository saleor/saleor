from ...utils import get_graphql_content

COLLECTION_ADD_PRODUCTS_MUTATION = """
mutation CollectionAssignProduct($id: ID!, $productIds: [ID!]!) {
  collectionAddProducts(collectionId: $id, products: $productIds) {
    errors {
      code
      message
      field
    }
    collection {
      id
      products(first: 5) {
        edges {
          node {
            id
          }
        }
      }
    }
  }
}
"""


def add_product_to_collection(
    staff_api_client,
    collection_id,
    products_ids,
):
    variables = {"id": collection_id, "productIds": products_ids}

    response = staff_api_client.post_graphql(
        COLLECTION_ADD_PRODUCTS_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    data = content["data"]["collectionAddProducts"]["collection"]
    assert content["data"]["collectionAddProducts"]["errors"] == []

    return data
