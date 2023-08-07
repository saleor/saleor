from ..utils import get_graphql_content

APP_CREATE_MUTATION = """
mutation AppCreate($input: AppInput!) {
  appCreate(input: $input) {
    errors {
      field
      message
      code
      permissions
    }
    authToken
    app {
      id
      name
    }
  }
}
"""


def create_app(
    staff_api_client,
    app_name,
    permissions,
):
    variables = {"input": {"name": app_name, "permissions": permissions}}

    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["appCreate"]["errors"] == []

    data = content["data"]["appCreate"]
    assert data["authToken"] is not None
    assert data["app"]["id"] is not None
    assert data["app"]["name"] == app_name

    return data
