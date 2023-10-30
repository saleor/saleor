from ...utils import get_graphql_content

VOUCHERS_QUERY = """
query vouchersQuery{
    vouchers(first: 10) {
    edges {
      node {
        id
      }
    }
  }
}
"""


def get_vouchers(
    api_client,
):
    response = api_client.post_graphql(VOUCHERS_QUERY)
    content = get_graphql_content(response)

    return content["data"]
