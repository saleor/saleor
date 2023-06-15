from .....graphql.tests.utils import get_graphql_content

PRODUCT_VARIANT_CREATE_MUTATION = """
mutation createVariant($input: ProductVariantCreateInput!) {
  productVariantCreate(input: $input) {
    errors {
      field
      message
      code
    }
    productVariant {
      id
      name
      product{
        id
      }
    }
  }
}
"""


def create_product_variant(staff_api_client, permissions, product_id, stocks=[]):
    variant_name = "Test product variant"
    variables = {
        "input": {
            "name": variant_name,
            "product": product_id,
            "attributes": [],
            "stocks": stocks,
        }
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CREATE_MUTATION,
        variables,
        permissions=permissions,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantCreate"]["productVariant"]
    assert data["id"] is not None
    assert data["name"] == variant_name
    assert data["product"]["id"] == product_id

    return data
