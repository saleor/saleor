from .....graphql.tests.utils import get_graphql_content

PRODUCT_TYPE_CREATE_MUTATION = """
mutation createProductType($input: ProductTypeInput!) {
  productTypeCreate(input: $input) {
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
    }
  }
}
"""


def create_digital_product_type(staff_api_client, permissions):
    product_type_name = "test type"
    slug = "test-type"
    variables = {
        "input": {
            "name": product_type_name,
            "slug": slug,
            "isShippingRequired": False,
            "isDigital": True,
        }
    }

    response = staff_api_client.post_graphql(
        PRODUCT_TYPE_CREATE_MUTATION, variables, permissions=permissions
    )
    content = get_graphql_content(response)

    assert content["data"]["productTypeCreate"]["errors"] == []

    data = content["data"]["productTypeCreate"]["productType"]
    assert data["id"] is not None
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["isShippingRequired"] is False
    assert data["isDigital"] is True

    return data
