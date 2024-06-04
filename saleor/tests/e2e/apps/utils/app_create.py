from ...utils import get_graphql_content

APP_CREATE_MUTATION = """
mutation AppCreate($input: AppInput!) {
  appCreate(input: $input) {
    errors {
      field
      code
      message
    }
    authToken
    app {
      id
      isActive
      identifier
    }
  }
}

"""


def add_app(
    staff_api_client,
    input,
):
    variables = {"input": input}

    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["appCreate"]["errors"] == []
    data = content["data"]["appCreate"]
    assert data["app"]["id"] is not None

    return data
