from ...utils import get_graphql_content

PRODUCT_ATTRIBUTE_ASSIGNMENT_UPDATE_MUTATION = """
mutation ProductAttributeAssignmentUpdate(
    $operations: [ProductAttributeAssignmentUpdateInput!]!, $id: ID!) {
  productAttributeAssignmentUpdate(operations: $operations, productTypeId: $id) {
    errors {
      field
      code
      message
    }
    productType {
      id
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
    }
  }
}
"""


def update_product_type_assignment_attribute(
    staff_api_client,
    product_type_id,
    operations,
):
    variables = {
        "id": product_type_id,
        "operations": operations,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_ATTRIBUTE_ASSIGNMENT_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    assert content["data"]["productAttributeAssignmentUpdate"]["errors"] == []

    data = content["data"]["productAttributeAssignmentUpdate"]["productType"]
    assert data["id"] is not None

    return data
