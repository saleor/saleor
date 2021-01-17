import graphene

from .....app.error_codes import AppErrorCode
from .....app.models import App
from ....tests.utils import assert_no_permission, get_graphql_content

APP_TOKEN_CREATE_MUTATION = """
mutation appTokenCreate($input: AppTokenInput!) {
  appTokenCreate(input: $input){
    authToken
    appToken{
      name
      authToken
      id
    }
    appErrors{
      field
      message
      code
    }
  }
}
"""


def test_app_token_create(
    permission_manage_apps, staff_api_client, staff_user, permission_manage_orders
):

    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = staff_api_client.post_graphql(
        query, variables={"input": variables}, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)
    token_data = content["data"]["appTokenCreate"]["appToken"]
    auth_token_data = content["data"]["appTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_app_token_create_for_app(
    permission_manage_apps,
    app_api_client,
    permission_manage_orders,
):

    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = app_api_client.post_graphql(
        query,
        variables={"input": variables},
        permissions=(permission_manage_apps,),
    )
    content = get_graphql_content(response)
    token_data = content["data"]["appTokenCreate"]["appToken"]
    auth_token_data = content["data"]["appTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_app_token_create_out_of_scope_app(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    permission_manage_orders,
):
    """Ensure user can't create token for app with wider scope of permissions."""
    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}

    response = staff_api_client.post_graphql(
        query,
        variables={"input": variables},
        permissions=(permission_manage_apps,),
    )
    content = get_graphql_content(response)

    data = content["data"]["appTokenCreate"]
    errors = data["appErrors"]
    assert not data["appToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "app"


def test_app_token_create_superuser_can_create_token_for_any_app(
    permission_manage_apps,
    superuser_api_client,
    permission_manage_orders,
):
    """Ensure superuser can create token for app with any scope of permissions."""
    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}

    response = superuser_api_client.post_graphql(query, variables={"input": variables})
    content = get_graphql_content(response)
    token_data = content["data"]["appTokenCreate"]["appToken"]
    auth_token_data = content["data"]["appTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_app_token_create_as_app_out_of_scope_app(
    permission_manage_apps,
    app_api_client,
    app,
    permission_manage_orders,
):
    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = app_api_client.post_graphql(
        query,
        variables={"input": variables},
        permissions=(permission_manage_apps,),
    )
    content = get_graphql_content(response)
    data = content["data"]["appTokenCreate"]
    errors = data["appErrors"]
    assert not data["appToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "app"


def test_app_token_create_no_permissions(staff_api_client, staff_user):
    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = staff_api_client.post_graphql(query, variables={"input": variables})
    assert_no_permission(response)
