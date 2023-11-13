from ...utils import get_graphql_content

ME_QUERY = """
query Me{
  me{
    id
    orders(first:10){
      edges{
        node{
          number
          status
        }
      }
    }
  }
}
"""


def get_own_data(api_client):
    variables = {}

    response = api_client.post_graphql(
        ME_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert data is not None

    return data
