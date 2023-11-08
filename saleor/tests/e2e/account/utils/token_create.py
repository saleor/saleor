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
      isActive
      isConfirmed
    }
  }
}
"""


def raw_token_create(
    e2e_not_logged_api_client,
    email,
    password,
):
    variables = {"email": email, "password": password}
    response = e2e_not_logged_api_client.post_graphql(
        TOKEN_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response, ignore_errors=True)

    return content


def token_create(
    e2e_not_logged_api_client,
    email,
    password,
):
    response = raw_token_create(
        e2e_not_logged_api_client,
        email,
        password,
    )
    data = response["data"]["tokenCreate"]
    assert data["errors"] == []

    assert data["token"] is not None
    assert data["refreshToken"] is not None

    user = data["user"]
    assert user["id"] is not None
    assert user["email"] == email

    return data
