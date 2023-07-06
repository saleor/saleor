from ...utils import get_graphql_content

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


def create_product_variant(
    staff_api_client,
    product_id,
    variant_name="Test product variant",
    stocks=None,
):
    if not stocks:
        stocks = []

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
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["productVariantCreate"]["errors"] == []

    data = content["data"]["productVariantCreate"]["productVariant"]
    assert data["id"] is not None
    assert data["name"] == variant_name
    assert data["product"]["id"] == product_id

    return data
