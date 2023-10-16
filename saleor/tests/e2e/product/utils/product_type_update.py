from ...utils import get_graphql_content

PRODUCT_TYPE_UPDATE_MUTATION = """
mutation ProductTypeUpdate($id: ID!, $input: ProductTypeInput!) {
  productTypeUpdate(id: $id, input: $input) {
    errors {
      field
      message
      code
    }
    productType {
      id
      name
      slug
      kind
      isShippingRequired
      isDigital
      hasVariants
      productAttributes {
        id
      }
      assignedVariantAttributes {
        attribute {
          id
        }
        variantSelection
      }
      taxClass {
        id
        name
      }
    }
    __typename
  }
}
"""


def update_product_type(
    staff_api_client,
    product_type_id,
    input,
):
    variables = {"id": product_type_id, "input": input}

    response = staff_api_client.post_graphql(PRODUCT_TYPE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["productTypeUpdate"]["errors"] == []

    data = content["data"]["productTypeUpdate"]["productType"]
    assert data["id"] is not None

    return data
