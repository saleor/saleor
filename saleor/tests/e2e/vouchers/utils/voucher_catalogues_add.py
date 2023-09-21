from ...utils import get_graphql_content

VOUCHER_CATALOGUE_ADD_MUTATION = """
mutation VoucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
  voucherCataloguesAdd(id: $id, input: $input) {
    errors {
      message
      field
    }
    voucher {
      id
      code
      type
      discountValueType
      channelListings { id }
      products(first: 10) {
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


def add_catalogue_to_voucher(
    staff_api_client,
    voucher_id,
    include_categories=False,
    include_collections=False,
    include_products=False,
    products=None,
    first=20,
):
    variables = {
        "id": voucher_id,
        "first": first,
        "includeCategories": include_categories,
        "includeCollections": include_collections,
        "includeProducts": include_products,
        "input": {"products": products},
    }

    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUE_ADD_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["voucherCataloguesAdd"]["errors"] == []

    data = content["data"]["voucherCataloguesAdd"]["voucher"]

    return data
