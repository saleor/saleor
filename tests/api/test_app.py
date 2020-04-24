import graphene
import pytest
from freezegun import freeze_time

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
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    superuser_api_client,
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

    # for staff user
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

    # for superuser
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
    app = App.objects.create(name="New_sa")
    AppToken.objects.create(app=app)
    query = APP_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_apps,
        permission_manage_products,
        permission_manage_users,
        permission_manage_orders,
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
    superuser_api_client,
    staff_user,
):
    """Ensure user cannot add permissions to app witch he doesn't have.

    Ensure that superuser pass restrictions.
    """
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

    # for staff user
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

    # for superuser
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
    app = App.objects.create(name="New_sa")
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
    superuser_api_client,
    staff_api_client,
    staff_user,
):
    """Ensure user cannot manage app with wider permission scope.

    Ensure that superuser pass restrictions.
    """
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

    # for staff user
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    errors = data["appErrors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name

    # for superuser
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
    app = App.objects.create(name="New_sa")
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
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_for_app(
    app_api_client, permission_manage_orders, permission_manage_apps,
):
    requestor = app_api_client.app
    app = App.objects.create(name="New_sa")
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
    staff_api_client,
    superuser_api_client,
    staff_user,
    app,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure user can't delete app with wider scope of permissions.

    Ensure superuser pass restriction.
    """
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}

    # for staff user
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

    # for superuser
    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["appErrors"]
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_for_app_out_of_scope_app(
    app_api_client, permission_manage_orders, permission_manage_apps,
):
    app = App.objects.create(name="New_sa")
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


QUERY_APPS_WITH_FILTER = """
    query ($filter: AppFilterInput ){
        apps(first: 5, filter: $filter){
            edges{
                node{
                    id
                    isActive
                    permissions{
                        name
                        code
                    }
                    tokens{
                        authToken
                    }
                    name
                }
            }
        }
    }
    """


@pytest.mark.parametrize(
    "app_filter, count", (({"search": "Sample"}, 1), ({"isActive": False}, 1), ({}, 2)),
)
def test_apps_query(
    staff_api_client, permission_manage_apps, app, app_filter, count,
):
    second_app = App.objects.create(name="Simple app")
    second_app.is_active = False
    second_app.tokens.create(name="default")
    second_app.save()

    variables = {"filter": app_filter}
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER, variables, permissions=[permission_manage_apps],
    )
    content = get_graphql_content(response)

    apps_data = content["data"]["apps"]["edges"]
    for app_data in apps_data:
        tokens = app_data["node"]["tokens"]
        assert len(tokens) == 1
        assert len(tokens[0]["authToken"]) == 4
    assert len(apps_data) == count


QUERY_APPS_WITH_SORT = """
    query ($sort_by: AppSortingInput!) {
        apps(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "apps_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["facebook", "google"]),
        ({"field": "NAME", "direction": "DESC"}, ["google", "facebook"]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, ["google", "facebook"]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, ["facebook", "google"]),
    ],
)
def test_query_apps_with_sort(
    apps_sort, result_order, staff_api_client, permission_manage_apps,
):
    with freeze_time("2018-05-31 12:00:01"):
        App.objects.create(name="google", is_active=True)
    with freeze_time("2019-05-31 12:00:01"):
        App.objects.create(name="facebook", is_active=True)
    variables = {"sort_by": apps_sort}
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(QUERY_APPS_WITH_SORT, variables)
    content = get_graphql_content(response)
    apps = content["data"]["apps"]["edges"]

    for order, account_name in enumerate(result_order):
        assert apps[order]["node"]["name"] == account_name


def test_apps_query_no_permission(
    staff_api_client, permission_manage_users, permission_manage_staff, app
):
    variables = {"filter": {}}
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER, variables, permissions=[]
    )
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


QUERY_APP = """
    query ($id: ID! ){
        app(id: $id){
            id
            created
            isActive
            permissions{
                code
                name
            }
            tokens{
                authToken
            }
            name
        }
    }
    """


def test_app_query(
    staff_api_client, permission_manage_apps, permission_manage_staff, app,
):
    app.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_APP, variables, permissions=[permission_manage_apps],
    )
    content = get_graphql_content(response)

    tokens = app.tokens.all()
    app_data = content["data"]["app"]
    tokens_data = app_data["tokens"]
    assert tokens.count() == 1
    assert tokens_data[0]["authToken"] == tokens.first().auth_token[-4:]

    assert app_data["isActive"] == app.is_active
    assert app_data["permissions"] == [
        {"code": "MANAGE_STAFF", "name": "Manage staff."}
    ]


def test_app_query_no_permission(
    staff_api_client, permission_manage_staff, permission_manage_users, app
):
    app.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_APP, variables, permissions=[])
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        QUERY_APP,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


def test_app_with_access_to_resources(
    app_api_client, app, permission_manage_orders, order_with_lines,
):
    query = """
      query {
        orders(first: 5) {
          edges {
            node {
              id
            }
          }
        }
      }
    """
    response = app_api_client.post_graphql(query)
    assert_no_permission(response)
    response = app_api_client.post_graphql(
        query, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)


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

    app = App.objects.create(name="New_sa")
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

    app = App.objects.create(name="New_sa")
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
    permission_manage_apps,
    staff_api_client,
    superuser_api_client,
    staff_user,
    permission_manage_orders,
):
    """Ensure user can't create token for app with wider scope of permissions.

    Ensure superuser pass restrictions.
    """
    app = App.objects.create(name="New_sa")
    query = APP_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"name": "Default token", "app": id}

    # for staff user
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

    # for superuser
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
    app = App.objects.create(name="New_sa")
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
    app = App.objects.create(name="New_sa", is_active=True)
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
    superuser_api_client,
    staff_user,
    app,
    permission_manage_products,
):
    """Ensure user can't delete app token with wider scope of permissions.

    Ensure superuser pass restrictions.
    """
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

    # for superuser
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
    app = App.objects.create(name="New_sa", is_active=True)
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
