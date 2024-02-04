from ...utils import get_graphql_content

PRODUCT_UPDATE_MUTATION = """
mutation ProductUpdate($id: ID!, $input: ProductInput!) {
  productUpdate(id: $id, input: $input) {
    errors {
      field
      message
      code
    }
    product {
      id
      name
      productType {
        id
      }
      category {
        id
      }
      attributes {
        attribute {
          id
        }
        values {
          name
        }
      }
      collections {
        id
      }
      taxClass {
        id
        name
      }
    }
  }
}
"""


def update_product(
    staff_api_client,
    product_id,
    input,
):
    variables = {"id": product_id, "input": input}

    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["productUpdate"]["errors"] == []

    data = content["data"]["productUpdate"]["product"]
    assert data["id"] is not None

    return data
