from ...utils import get_graphql_content

USER_QUERY = """
query CustomerDetails($id:ID!){
  user(id: $id) {
    id
    email
    isConfirmed
    isActive
    orders(first: 10){
      edges {
        node {
          id
          number
          paymentStatus
          created
        }
      }
    }
  }
}
"""


def get_user(
    staff_api_client,
    user_id,
):
    variables = {"id": user_id}

    response = staff_api_client.post_graphql(
        USER_QUERY,
        variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["user"]

    return data
