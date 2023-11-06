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

    assert response["data"]["tokenCreate"]["errors"] == []

    assert response["data"]["tokenCreate"]["token"] is not None
    assert response["data"]["tokenCreate"]["refreshToken"] is not None

    data = response["data"]["tokenCreate"]["user"]
    assert data["id"] is not None
    assert data["email"] == email

    return data
