from ...utils import get_graphql_content

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
    }
  }
}
"""


def create_product(
    staff_api_client,
    product_type_id,
    category_id,
    product_name="Test product",
    attributes=None,
    collection_ids=None,
):
    if not attributes:
        attributes = []

    if not collection_ids:
        collection_ids = []

    variables = {
        "input": {
            "name": product_name,
            "productType": product_type_id,
            "category": category_id,
            "attributes": attributes,
            "collections": collection_ids,
        }
    }

    response = staff_api_client.post_graphql(
        PRODUCT_CREATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["productCreate"]["errors"] == []

    data = content["data"]["productCreate"]["product"]
    assert data["id"] is not None
    assert data["name"] == product_name
    assert data["productType"]["id"] == product_type_id
    assert data["category"]["id"] == category_id

    return data
