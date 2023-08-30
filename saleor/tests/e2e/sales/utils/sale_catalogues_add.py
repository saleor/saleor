from ...utils import get_graphql_content

SALE_CATALOGUES_ADD_MUTATION = """
mutation SaleCataloguesAdd($id: ID!, $input: CatalogueInput!, $first: Int) {
  saleCataloguesAdd(id: $id, input: $input) {
    errors {
      field
      message
      code
    }
    sale {
      id
      name
      channelListings {
        channel {
          id
        }
        discountValue
      }
      categories(first: $first) {
        edges {
          node {
            id
          }
        }
      }
      collections(first: $first) {
        edges {
          node {
            id
          }
        }
      }
      products(first: $first) {
        edges {
          node {
            id
          }
        }
      }
      variants(first: $first) {
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


def sale_catalogues_add(
    staff_api_client,
    sale_id,
    input,
    first=1,
):
    variables = {"id": sale_id, "first": first, "input": input}

    response = staff_api_client.post_graphql(
        SALE_CATALOGUES_ADD_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["saleCataloguesAdd"]["errors"] == []
    data = content["data"]["saleCataloguesAdd"]["sale"]

    return data
