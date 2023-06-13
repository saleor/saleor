from .....graphql.tests.utils import get_graphql_content

PRODUCT_CREATE_MUTATION = """
mutation createProduct($input: ProductCreateInput!) {
  productCreate(input: $input) {
    errors {
      field
      code
      message
    }
    product {
      id
      name
      productType{
        id
      }
    }
  }
}
"""


def create_product(staff_api_client, permissions, product_type_id):
    product_name = "Test product"
    variables = {
        "input": {
            "name": product_name,
            "productType": product_type_id,
        }
    }
    response = staff_api_client.post_graphql(
        PRODUCT_CREATE_MUTATION,
        variables,
        permissions=permissions,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]["product"]
    assert data["name"] == product_name
    assert data["productType"]["id"] == product_type_id

    return data
