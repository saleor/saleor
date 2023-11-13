from ...utils import get_graphql_content

ACCOUNT_REGISTER_MUTATION = """
mutation AccountRegister($input: AccountRegisterInput!) {
  accountRegister(input: $input) {
    errors {
      field
      message
      code
    }
    requiresConfirmation
    user {
      id
      email
      isActive
    }
  }
}
"""


def raw_account_register(
    e2e_not_logged_api_client,
    email,
    password,
    channel_slug,
    redirect_url=None,
):
    variables = {
        "input": {
            "email": email,
            "password": password,
            "channel": channel_slug,
            "redirectUrl": redirect_url,
        }
    }

    response = e2e_not_logged_api_client.post_graphql(
        ACCOUNT_REGISTER_MUTATION,
        variables,
    )
    content = get_graphql_content(response, ignore_errors=True)

    return content


def account_register(
    e2e_not_logged_api_client,
    email,
    password,
    channel_slug,
    redirect_url=None,
):
    response = raw_account_register(
        e2e_not_logged_api_client,
        email,
        password,
        channel_slug,
        redirect_url,
    )
    assert response["data"]["accountRegister"]["errors"] == []

    data = response["data"]["accountRegister"]
    assert data["user"]["id"] is not None
    assert data["user"]["email"] == email

    return data
