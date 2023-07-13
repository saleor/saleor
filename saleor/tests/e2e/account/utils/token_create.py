from ...utils import get_graphql_content

TOKEN_CREATE_MUTATION = """
mutation TokenCreate($email: String!, $password: String!) {
  tokenCreate(email: $email, password: $password) {
    errors {
      field
      message
      code
    }
    token
    refreshToken
    user {
      id
      email
    }
  }
}
"""


def token_create(
    e2e_not_logged_api_client,
    email,
    password,
):
    variables = {"email": email, "password": password}

    response = e2e_not_logged_api_client.post_graphql(
        TOKEN_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["tokenCreate"]["errors"] == []

    assert content["data"]["tokenCreate"]["token"] is not None
    assert content["data"]["tokenCreate"]["refreshToken"] is not None

    data = content["data"]["tokenCreate"]["user"]
    assert data["id"] is not None
    assert data["email"] == email

    return data
