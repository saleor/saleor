import graphene

from saleor.app.models import App, AppToken
from saleor.graphql.core.enums import PermissionEnum

from .utils import assert_no_permission, get_graphql_content

APP_CREATE_MUTATION = """
    mutation AppCreate(
        $name: String, $is_active: Boolean $permissions: [PermissionEnum]){
        appCreate(input:
            {name: $name, isActive: $is_active, permissions: $permissions})
        {
            authToken
            app{
                permissions{
                    code
                    name
                }
                id
                isActive
                name
                tokens{
                    authToken
                }
            }
            errors{
                field
                message
            }
        }
    }
    """


def test_app_create_mutation(
    permission_manage_apps, permission_manage_products, staff_api_client, staff_user,
):
    query = APP_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_apps)

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    app_data = content["data"]["appCreate"]["app"]
    default_token = content["data"]["appCreate"]["authToken"]
    app = App.objects.get()
    assert app_data["isActive"] == app.is_active
    assert app_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token == app.tokens.get().auth_token


def test_app_create_mutation_no_permissions(
    permission_manage_apps, permission_manage_products, staff_api_client, staff_user,
):
    query = APP_CREATE_MUTATION
    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


APP_UPDATE_MUTATION = """
mutation AppUpdate($id: ID!, $is_active: Boolean,
                                $permissions: [PermissionEnum]){
    appUpdate(id: $id,
        input:{isActive: $is_active, permissions:$permissions}){
        app{
            isActive
            id
            permissions{
                code
                name
            }
            tokens{
                authToken
            }
            name
        }
        errors{
            field
            message
        }
    }
}
"""


def test_app_update_mutation(
    app,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    query = APP_UPDATE_MUTATION
    staff_user.user_permissions.add(permission_manage_apps)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    app_data = content["data"]["appUpdate"]["app"]
    tokens_data = app_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert app_data["isActive"] == app.is_active
    assert app.is_active is False
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_app_update_no_permission(app, staff_api_client, staff_user):
    query = APP_UPDATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
        "is_active": False,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


APP_TOKEN_CREATE_MUTATION = """
mutation appTokenCreate($input: AppTokenInput!) {
  appTokenCreate(input: $input){
    authToken
    appToken{
      name
      authToken
      id
    }
    errors{
      field
      message
    }
  }
}
"""


def test_app_token_create(permission_manage_apps, staff_api_client, staff_user):

    app = App.objects.create(name="New_sa")
    query = APP_TOKEN_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_apps)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = staff_api_client.post_graphql(query, variables={"input": variables})
    content = get_graphql_content(response)
    token_data = content["data"]["appTokenCreate"]["appToken"]
    auth_token_data = content["data"]["appTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_app_token_create_no_permissions(staff_api_client, staff_user):
    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = staff_api_client.post_graphql(query, variables={"input": variables})
    assert_no_permission(response)


APP_TOKEN_DELETE_MUTATION = """
    mutation appTokenDelete($id: ID!){
      appTokenDelete(id: $id){
        errors{
          field
          message
        }
        appToken{
          name
          authToken
        }
      }
    }
"""


def test_app_token_delete(permission_manage_apps, staff_api_client, staff_user, app):

    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    id = graphene.Node.to_global_id("AppToken", token.id)
    staff_user.user_permissions.add(permission_manage_apps)

    variables = {"id": id}
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    assert not AppToken.objects.filter(id=token.id).first()


def test_app_token_delete_no_permissions(staff_api_client, staff_user, app):

    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    token.refresh_from_db()
