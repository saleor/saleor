from .....app.error_codes import AppErrorCode
from .....app.models import App
from ....core.enums import PermissionEnum
from ....tests.utils import assert_no_permission, get_graphql_content

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
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    staff_user,
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
    permission_manage_apps,
    permission_manage_products,
    app_api_client,
    staff_user,
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
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    staff_user,
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
    permission_manage_apps,
    permission_manage_products,
    superuser_api_client,
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
    permission_manage_apps,
    permission_manage_products,
    app_api_client,
    staff_user,
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
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    staff_user,
):
    query = APP_CREATE_MUTATION
    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
