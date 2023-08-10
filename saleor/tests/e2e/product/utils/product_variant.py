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
      quantityLimitPerCustomer
      product{
        id
      }
    }
  }
}
"""


def raw_create_product_variant(
    staff_api_client,
    product_id,
    variant_name="Test product variant",
    stocks=None,
    quantity_limit_per_customer=10,
):
    if not stocks:
        stocks = []

    variables = {
        "input": {
            "name": variant_name,
            "product": product_id,
            "attributes": [],
            "stocks": stocks,
            "quantityLimitPerCustomer": quantity_limit_per_customer,
        }
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CREATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantCreate"]

    return data


def create_product_variant(
    staff_api_client,
    product_id,
    variant_name="Test product variant",
    stocks=None,
    quantity_limit_per_customer=10,
):
    response = raw_create_product_variant(
        staff_api_client,
        product_id,
        variant_name,
        stocks,
        quantity_limit_per_customer,
    )

    assert response["errors"] == []

    data = response["productVariant"]
    assert data["id"] is not None
    assert data["name"] == variant_name
    assert data["product"]["id"] == product_id

    return data
