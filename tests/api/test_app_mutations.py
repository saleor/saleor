import graphene

from saleor.app.error_codes import AppErrorCode
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
            appErrors{
                field
                message
                code
                permissions
            }
        }
    }
    """


def test_app_create_mutation(
    permission_manage_apps, permission_manage_products, staff_api_client, staff_user,
):
    query = APP_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_products)

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)
    app_data = content["data"]["appCreate"]["app"]
    default_token = content["data"]["appCreate"]["authToken"]
    app = App.objects.get()
    assert app_data["isActive"] == app.is_active
    assert app_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token == app.tokens.get().auth_token


def test_app_create_mutation_for_app(
    permission_manage_apps, permission_manage_products, app_api_client, staff_user,
):
    query = APP_CREATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_apps, permission_manage_products)

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    app_data = content["data"]["appCreate"]["app"]
    default_token = content["data"]["appCreate"]["authToken"]
    app = App.objects.exclude(pk=requestor.pk).get()
    assert app_data["isActive"] == app.is_active
    assert app_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token == app.tokens.get().auth_token


def test_app_create_mutation_out_of_scope_permissions(
    permission_manage_apps, permission_manage_products, staff_api_client, staff_user,
):
    """Ensure user can't create app with permissions out of user's scope.

    Ensure superuser pass restrictions.
    """
    query = APP_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_apps)

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }

    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]

    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_PRODUCTS.name]


def test_app_create_mutation_superuser_can_create_app_with_any_perms(
    permission_manage_apps, permission_manage_products, superuser_api_client,
):
    """Ensure superuser can create app with any permissions."""
    query = APP_CREATE_MUTATION

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    app_data = content["data"]["appCreate"]["app"]
    default_token = content["data"]["appCreate"]["authToken"]
    app = App.objects.get()
    assert app_data["isActive"] == app.is_active
    assert app_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token == app.tokens.get().auth_token


def test_app_create_mutation_for_app_out_of_scope_permissions(
    permission_manage_apps, permission_manage_products, app_api_client, staff_user,
):
    query = APP_CREATE_MUTATION

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]

    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_PRODUCTS.name]


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
        appErrors{
            field
            message
            code
            permissions
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
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
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


def test_app_update_mutation_for_app(
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    query = APP_UPDATE_MUTATION

    app = App.objects.create(name="New_app")
    app.permissions.add(permission_manage_orders)
    AppToken.objects.create(app=app)

    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_apps,
        permission_manage_products,
        permission_manage_users,
        permission_manage_orders,
    )
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = app_api_client.post_graphql(query, variables=variables)
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


def test_app_update_mutation_out_of_scope_permissions(
    app,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    """Ensure user cannot add permissions to app witch he doesn't have."""
    query = APP_UPDATE_MUTATION
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_products)
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

    data = content["data"]["appUpdate"]
    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_USERS.name]


def test_app_update_mutation_superuser_can_add_any_permissions_to_app(
    app,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
    superuser_api_client,
):
    """Ensure superuser can add any permissions to app."""
    query = APP_UPDATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    app_data = data["app"]
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


def test_app_update_mutation_for_app_out_of_scope_permissions(
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    app = App.objects.create(name="New_app")
    query = APP_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_apps, permission_manage_products, permission_manage_orders,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_USERS.name]


def test_app_update_mutation_out_of_scope_app(
    app,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    """Ensure user cannot manage app with wider permission scope."""
    query = APP_UPDATE_MUTATION
    staff_user.user_permissions.add(
        permission_manage_apps, permission_manage_products, permission_manage_users,
    )
    app.permissions.add(permission_manage_orders)
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

    data = content["data"]["appUpdate"]
    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name


def test_app_update_mutation_superuser_can_update_any_app(
    app,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    superuser_api_client,
):
    """Ensure superuser can manage any app."""
    query = APP_UPDATE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    app_data = data["app"]
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


def test_app_update_mutation_for_app_out_of_scope_app(
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    app = App.objects.create(name="New_app")
    query = APP_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_apps, permission_manage_products, permission_manage_users,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name


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


APP_DELETE_MUTATION = """
    mutation appDelete($id: ID!){
      appDelete(id: $id){
        appErrors{
          field
          message
          code
        }
        app{
          name
        }
      }
    }
"""


def test_app_delete(
    staff_api_client, staff_user, app, permission_manage_orders, permission_manage_apps,
):
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    staff_user.user_permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["appErrors"]
    assert not App.objects.filter(id=app.id)


def test_app_delete_for_app(
    app_api_client, permission_manage_orders, permission_manage_apps,
):
    requestor = app_api_client.app
    app = App.objects.create(name="New_app")
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    requestor.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["appErrors"]
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_out_of_scope_app(
    staff_api_client, staff_user, app, permission_manage_apps, permission_manage_orders,
):
    """Ensure user can't delete app with wider scope of permissions."""
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"


def test_app_delete_superuser_can_delete_any_app(
    superuser_api_client, app, permission_manage_apps, permission_manage_orders,
):
    """Ensure superuser can delete app with any scope of permissions."""
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["appErrors"]
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_for_app_out_of_scope_app(
    app_api_client, permission_manage_orders, permission_manage_apps,
):
    app = App.objects.create(name="New_app")
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"


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
    permission_manage_apps, app_api_client, permission_manage_orders,
):

    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = app_api_client.post_graphql(
        query, variables={"input": variables}, permissions=(permission_manage_apps,),
    )
    content = get_graphql_content(response)
    token_data = content["data"]["appTokenCreate"]["appToken"]
    auth_token_data = content["data"]["appTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_app_token_create_out_of_scope_app(
    permission_manage_apps, staff_api_client, staff_user, permission_manage_orders,
):
    """Ensure user can't create token for app with wider scope of permissions."""
    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}

    response = staff_api_client.post_graphql(
        query, variables={"input": variables}, permissions=(permission_manage_apps,),
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
    permission_manage_apps, superuser_api_client, permission_manage_orders,
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
    permission_manage_apps, app_api_client, app, permission_manage_orders,
):
    app = App.objects.create(name="New_app")
    query = APP_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}
    response = app_api_client.post_graphql(
        query, variables={"input": variables}, permissions=(permission_manage_apps,),
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


APP_TOKEN_DELETE_MUTATION = """
    mutation appTokenDelete($id: ID!){
      appTokenDelete(id: $id){
        appErrors{
          field
          message
          code
        }
        appToken{
          name
          authToken
        }
      }
    }
"""


def test_app_token_delete(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app,
    permission_manage_products,
):

    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    staff_user.user_permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)
    staff_user.user_permissions.add(permission_manage_apps)

    variables = {"id": id}
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    assert not AppToken.objects.filter(id=token.id).first()


def test_app_token_delete_for_app(
    permission_manage_apps, app_api_client, permission_manage_products,
):
    app = App.objects.create(name="New_app", is_active=True)
    token = AppToken.objects.create(app=app)
    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
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


def test_app_token_delete_out_of_scope_app(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app,
    permission_manage_products,
):
    """Ensure user can't delete app token with wider scope of permissions."""
    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appTokenDelete"]
    errors = data["appErrors"]

    assert not data["appToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"
    assert AppToken.objects.filter(id=token.id).exists()


def test_app_token_delete_superuser_can_delete_token_for_any_app(
    permission_manage_apps, superuser_api_client, app, permission_manage_products,
):
    """Ensure superuser can delete app token for app with any scope of permissions."""
    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appTokenDelete"]
    errors = data["appErrors"]

    assert data["appToken"]
    assert not errors
    assert not AppToken.objects.filter(id=token.id).exists()


def test_app_token_delete_for_app_out_of_scope_app(
    permission_manage_apps, app_api_client, permission_manage_products,
):
    app = App.objects.create(name="New_app", is_active=True)
    token = AppToken.objects.create(app=app)
    query = APP_TOKEN_DELETE_MUTATION
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appTokenDelete"]
    errors = data["appErrors"]

    assert not data["appToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"
    assert AppToken.objects.filter(id=token.id).exists()
