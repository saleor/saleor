import graphene
import pytest
from django.contrib.auth.models import Permission
from freezegun import freeze_time

from saleor.account.error_codes import AccountErrorCode
from saleor.app.models import App, AppToken
from saleor.graphql.core.enums import PermissionEnum

from .utils import assert_no_permission, get_graphql_content


@pytest.fixture
def permission_manage_service_accounts():
    return Permission.objects.get(codename="manage_apps")


SERVICE_ACCOUNT_CREATE_MUTATION = """
    mutation ServiceAccountCreate(
        $name: String, $is_active: Boolean $permissions: [PermissionEnum]){
        serviceAccountCreate(input:
            {name: $name, isActive: $is_active, permissions: $permissions})
        {
            authToken
            serviceAccount{
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
            accountErrors{
                field
                message
                code
            }
        }
    }
    """


def test_service_account_create_mutation(
    permission_manage_service_accounts,
    permission_manage_products,
    staff_api_client,
    staff_user,
):
    query = SERVICE_ACCOUNT_CREATE_MUTATION
    staff_user.user_permissions.add(
        permission_manage_service_accounts, permission_manage_products
    )

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    service_account_data = content["data"]["serviceAccountCreate"]["serviceAccount"]
    default_token = content["data"]["serviceAccountCreate"]["authToken"]
    app = App.objects.get()
    assert service_account_data["isActive"] == app.is_active
    assert service_account_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token == app.tokens.get().auth_token


def test_service_account_create_mutation_for_service_account(
    permission_manage_service_accounts,
    permission_manage_products,
    app_api_client,
    staff_user,
):
    query = SERVICE_ACCOUNT_CREATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_service_accounts, permission_manage_products
    )

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    service_account_data = content["data"]["serviceAccountCreate"]["serviceAccount"]
    default_token = content["data"]["serviceAccountCreate"]["authToken"]
    app = App.objects.exclude(pk=requestor.pk).get()
    assert service_account_data["isActive"] == app.is_active
    assert service_account_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token == app.tokens.get().auth_token


def test_service_account_create_mutation_out_of_scope_permissions(
    permission_manage_service_accounts,
    permission_manage_products,
    staff_api_client,
    superuser_api_client,
    staff_user,
):
    """Ensure user can't create service account with permissions out of user's scope.

    Ensure superuser pass restrictions.
    """
    query = SERVICE_ACCOUNT_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_service_accounts)

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }

    # for staff user
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    data = content["data"]["serviceAccountCreate"]

    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_PERMISSION.name

    # for superuser
    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    service_account_data = content["data"]["serviceAccountCreate"]["serviceAccount"]
    default_token = content["data"]["serviceAccountCreate"]["authToken"]
    app = App.objects.get()
    assert service_account_data["isActive"] == app.is_active
    assert service_account_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token == app.tokens.get().auth_token


def test_service_account_create_mutation_for_service_account_out_of_scope_permissions(
    permission_manage_service_accounts,
    permission_manage_products,
    app_api_client,
    staff_user,
):
    query = SERVICE_ACCOUNT_CREATE_MUTATION

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)
    data = content["data"]["serviceAccountCreate"]

    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_PERMISSION.name


def test_service_account_create_mutation_no_permissions(
    permission_manage_service_accounts,
    permission_manage_products,
    staff_api_client,
    staff_user,
):
    query = SERVICE_ACCOUNT_CREATE_MUTATION
    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


SERVICE_ACCOUNT_UPDATE_MUTATION = """
mutation ServiceAccountUpdate($id: ID!, $is_active: Boolean,
                                $permissions: [PermissionEnum]){
    serviceAccountUpdate(id: $id,
        input:{isActive: $is_active, permissions:$permissions}){
        serviceAccount{
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
        accountErrors{
            field
            message
            code
        }
    }
}
"""


def test_service_account_update_mutation(
    app,
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    staff_user.user_permissions.add(
        permission_manage_products, permission_manage_users, permission_manage_orders,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)

    service_account_data = content["data"]["serviceAccountUpdate"]["serviceAccount"]
    tokens_data = service_account_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert service_account_data["isActive"] == app.is_active
    assert app.is_active is False
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_service_account_update_mutation_for_service_account(
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    app = App.objects.create(name="New_sa")
    AppToken.objects.create(app=app)
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_service_accounts,
        permission_manage_products,
        permission_manage_users,
        permission_manage_orders,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

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

    service_account_data = content["data"]["serviceAccountUpdate"]["serviceAccount"]
    tokens_data = service_account_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert service_account_data["isActive"] == app.is_active
    assert app.is_active is False
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_service_account_update_mutation_out_of_scope_permissions(
    app,
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    superuser_api_client,
    staff_user,
):
    """Ensure user cannot add permissions to service account witch he doesn't have.

    Ensure that superuser pass restrictions.
    """
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    staff_user.user_permissions.add(
        permission_manage_service_accounts, permission_manage_products
    )
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

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

    data = content["data"]["serviceAccountUpdate"]
    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_PERMISSION.name

    # for superuser
    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountUpdate"]
    service_account_data = data["serviceAccount"]
    tokens_data = service_account_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert service_account_data["isActive"] == app.is_active
    assert app.is_active is False
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_service_account_update_mutation_for_service_account_out_of_scope_permissions(
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_service_accounts,
        permission_manage_products,
        permission_manage_orders,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

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

    data = content["data"]["serviceAccountUpdate"]
    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_PERMISSION.name


def test_service_account_update_mutation_out_of_scope_service_account(
    app,
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    superuser_api_client,
    staff_api_client,
    staff_user,
):
    """Ensure user cannot manage service account with wider permission scope.

    Ensure that superuser pass restrictions.
    """
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    staff_user.user_permissions.add(
        permission_manage_service_accounts,
        permission_manage_products,
        permission_manage_users,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

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

    data = content["data"]["serviceAccountUpdate"]
    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name

    # for superuser
    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountUpdate"]
    service_account_data = data["serviceAccount"]
    tokens_data = service_account_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert service_account_data["isActive"] == app.is_active
    assert app.is_active is False
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_service_account_update_mutation_for_service_account_out_of_scope_service_acc(
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_service_accounts,
        permission_manage_products,
        permission_manage_users,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

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

    data = content["data"]["serviceAccountUpdate"]
    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name


def test_service_account_update_no_permission(app, staff_api_client, staff_user):
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {
        "id": id,
        "is_active": False,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


SERVICE_ACCOUNT_DELETE_MUTATION = """
    mutation serviceAccountDelete($id: ID!){
      serviceAccountDelete(id: $id){
        accountErrors{
          field
          message
          code
        }
        serviceAccount{
          name
        }
      }
    }
"""


def test_service_account_delete(
    staff_api_client,
    staff_user,
    app,
    permission_manage_orders,
    permission_manage_service_accounts,
):
    query = SERVICE_ACCOUNT_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    staff_user.user_permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountDelete"]
    assert data["serviceAccount"]
    assert not data["accountErrors"]
    assert not App.objects.filter(id=app.id).exists()


def test_service_account_delete_for_app(
    app_api_client, permission_manage_orders, permission_manage_service_accounts,
):
    requestor = app_api_client.app
    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    requestor.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountDelete"]
    assert data["serviceAccount"]
    assert not data["accountErrors"]
    assert not App.objects.filter(id=app.id).exists()


def test_service_account_delete_out_of_scope_app(
    staff_api_client,
    superuser_api_client,
    staff_user,
    app,
    permission_manage_service_accounts,
    permission_manage_orders,
):
    """Ensure user can't delete service account with wider scope of permissions.

    Ensure superuser pass restriction
    """
    query = SERVICE_ACCOUNT_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

    variables = {"id": id}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountDelete"]
    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name
    assert error["field"] == "id"

    # for superuser
    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountDelete"]
    assert data["serviceAccount"]
    assert not data["accountErrors"]
    assert not App.objects.filter(id=app.id).exists()


def test_service_account_delete_for_service_account_out_of_scope_service_account(
    app_api_client, permission_manage_orders, permission_manage_service_accounts,
):
    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountDelete"]
    errors = data["accountErrors"]
    assert not data["serviceAccount"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name
    assert error["field"] == "id"


QUERY_SERVICE_ACCOUNTS_WITH_FILTER = """
    query ($filter: ServiceAccountFilterInput ){
        serviceAccounts(first: 5, filter: $filter){
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
    "service_account_filter, count",
    (({"search": "Sample"}, 1), ({"isActive": False}, 1), ({}, 2)),
)
def test_service_accounts_query(
    staff_api_client,
    permission_manage_service_accounts,
    app,
    service_account_filter,
    count,
):
    second_app = App.objects.create(name="Simple service")
    second_app.is_active = False
    second_app.tokens.create(name="default")
    second_app.save()

    variables = {"filter": service_account_filter}
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNTS_WITH_FILTER,
        variables,
        permissions=[permission_manage_service_accounts],
    )
    content = get_graphql_content(response)

    service_accounts_data = content["data"]["serviceAccounts"]["edges"]
    for service_account_data in service_accounts_data:
        tokens = service_account_data["node"]["tokens"]
        assert len(tokens) == 1
        assert len(tokens[0]["authToken"]) == 4
    assert len(service_accounts_data) == count


QUERY_SERVICE_ACCOUNTS_WITH_SORT = """
    query ($sort_by: ServiceAccountSortingInput!) {
        serviceAccounts(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "service_accounts_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["facebook", "google"]),
        ({"field": "NAME", "direction": "DESC"}, ["google", "facebook"]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, ["google", "facebook"]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, ["facebook", "google"]),
    ],
)
def test_query_service_accounts_with_sort(
    service_accounts_sort,
    result_order,
    staff_api_client,
    permission_manage_service_accounts,
):
    with freeze_time("2018-05-31 12:00:01"):
        App.objects.create(name="google", is_active=True)
    with freeze_time("2019-05-31 12:00:01"):
        App.objects.create(name="facebook", is_active=True)
    variables = {"sort_by": service_accounts_sort}
    staff_api_client.user.user_permissions.add(permission_manage_service_accounts)
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNTS_WITH_SORT, variables
    )
    content = get_graphql_content(response)
    service_accounts = content["data"]["serviceAccounts"]["edges"]

    for order, account_name in enumerate(result_order):
        assert service_accounts[order]["node"]["name"] == account_name


def test_service_accounts_query_no_permission(
    staff_api_client, permission_manage_users, permission_manage_staff, app
):
    variables = {"filter": {}}
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNTS_WITH_FILTER, variables, permissions=[]
    )
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNTS_WITH_FILTER,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


QUERY_SERVICE_ACCOUNT = """
    query ($id: ID! ){
        serviceAccount(id: $id){
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


def test_service_account_query(
    staff_api_client, permission_manage_service_accounts, permission_manage_staff, app,
):
    app.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT,
        variables,
        permissions=[permission_manage_service_accounts],
    )
    content = get_graphql_content(response)

    tokens = app.tokens.all()
    service_account_data = content["data"]["serviceAccount"]
    tokens_data = service_account_data["tokens"]
    assert tokens.count() == 1
    assert tokens_data[0]["authToken"] == tokens.first().auth_token[-4:]

    assert service_account_data["isActive"] == app.is_active
    assert service_account_data["permissions"] == [
        {"code": "MANAGE_STAFF", "name": "Manage staff."}
    ]


def test_service_account_query_no_permission(
    staff_api_client, permission_manage_staff, permission_manage_users, app
):
    app.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT, variables, permissions=[]
    )
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


def test_service_account_with_access_to_resources(
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


SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION = """
mutation serviceAccountTokenCreate($input: ServiceAccountTokenInput!) {
  serviceAccountTokenCreate(input: $input){
    authToken
    serviceAccountToken{
      name
      authToken
      id
    }
    accountErrors{
      field
      message
      code
    }
  }
}
"""


def test_service_account_token_create(
    permission_manage_service_accounts,
    staff_api_client,
    staff_user,
    permission_manage_orders,
):
    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {"name": "Default token", "serviceAccount": id}
    response = staff_api_client.post_graphql(
        query,
        variables={"input": variables},
        permissions=(permission_manage_service_accounts,),
    )
    content = get_graphql_content(response)
    token_data = content["data"]["serviceAccountTokenCreate"]["serviceAccountToken"]
    auth_token_data = content["data"]["serviceAccountTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_service_account_token_create_for_app(
    permission_manage_service_accounts, app_api_client, permission_manage_orders,
):

    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {"name": "Default token", "serviceAccount": id}
    response = app_api_client.post_graphql(
        query,
        variables={"input": variables},
        permissions=(permission_manage_service_accounts,),
    )
    content = get_graphql_content(response)
    token_data = content["data"]["serviceAccountTokenCreate"]["serviceAccountToken"]
    auth_token_data = content["data"]["serviceAccountTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_service_account_token_create_out_of_scope_service_account(
    permission_manage_service_accounts,
    staff_api_client,
    superuser_api_client,
    staff_user,
    permission_manage_orders,
):
    """Ensure user can't create token for service account with wider
    scope of permissions.

    Ensure superuser pass restrictions.
    """
    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {"name": "Default token", "serviceAccount": id}

    # for staff user
    response = staff_api_client.post_graphql(
        query,
        variables={"input": variables},
        permissions=(permission_manage_service_accounts,),
    )
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountTokenCreate"]
    errors = data["accountErrors"]
    assert not data["serviceAccountToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name
    assert error["field"] == "serviceAccount"

    # for superuser
    response = superuser_api_client.post_graphql(query, variables={"input": variables})
    content = get_graphql_content(response)
    token_data = content["data"]["serviceAccountTokenCreate"]["serviceAccountToken"]
    auth_token_data = content["data"]["serviceAccountTokenCreate"]["authToken"]
    auth_token = app.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_service_account_token_create_as_service_account_out_of_scope_service_account(
    permission_manage_service_accounts, app_api_client, app, permission_manage_orders,
):

    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION
    app.permissions.add(permission_manage_orders)

    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {"name": "Default token", "serviceAccount": id}
    response = app_api_client.post_graphql(
        query,
        variables={"input": variables},
        permissions=(permission_manage_service_accounts,),
    )
    content = get_graphql_content(response)
    data = content["data"]["serviceAccountTokenCreate"]
    errors = data["accountErrors"]
    assert not data["serviceAccountToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name
    assert error["field"] == "serviceAccount"


def test_service_account_token_create_no_permissions(staff_api_client, staff_user):
    app = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION
    id = graphene.Node.to_global_id("ServiceAccount", app.id)
    variables = {"name": "Default token", "serviceAccount": id}
    response = staff_api_client.post_graphql(query, variables={"input": variables})
    assert_no_permission(response)


SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION = """
    mutation serviceAccountTokenDelete($id: ID!){
      serviceAccountTokenDelete(id: $id){
        accountErrors{
          field
          message
          code
        }
        serviceAccountToken{
          name
          authToken
        }
      }
    }
"""


def test_service_account_token_delete(
    permission_manage_service_accounts,
    permission_manage_products,
    staff_api_client,
    staff_user,
    app,
):

    query = SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    staff_user.user_permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("ServiceAccountToken", token.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    get_graphql_content(response)
    assert not AppToken.objects.filter(id=token.id).first()


def test_service_account_token_delete_for_app(
    permission_manage_service_accounts, app_api_client, permission_manage_products,
):
    app = App.objects.create(name="New_sa", is_active=True)
    token = AppToken.objects.create(app=app)
    query = SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("ServiceAccountToken", token.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    get_graphql_content(response)
    assert not AppToken.objects.filter(id=token.id).first()


def test_service_account_token_delete_no_permissions(staff_api_client, staff_user, app):

    query = SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    id = graphene.Node.to_global_id("ServiceAccountToken", token.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    token.refresh_from_db()


def test_service_account_token_delete_out_of_scope_service_account(
    permission_manage_service_accounts,
    staff_api_client,
    superuser_api_client,
    staff_user,
    app,
    permission_manage_products,
):
    """Ensure user can't delete service account token with wider scope of permissions.

    Ensure superuser pass restrictions.
    """
    query = SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("ServiceAccountToken", token.id)

    variables = {"id": id}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountTokenDelete"]
    errors = data["accountErrors"]

    assert not data["serviceAccountToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name
    assert error["field"] == "id"
    assert AppToken.objects.filter(id=token.id).exists()

    # for superuser
    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountTokenDelete"]
    errors = data["accountErrors"]

    assert data["serviceAccountToken"]
    assert not errors
    assert not AppToken.objects.filter(id=token.id).exists()


def test_service_account_token_delete_for_service_account_out_of_scope_app(
    permission_manage_service_accounts, app_api_client, permission_manage_products,
):
    app = App.objects.create(name="New_sa", is_active=True)
    token = AppToken.objects.create(app=app)
    query = SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("ServiceAccountToken", token.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_service_accounts,)
    )
    content = get_graphql_content(response)

    data = content["data"]["serviceAccountTokenDelete"]
    errors = data["accountErrors"]

    assert not data["serviceAccountToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.OUT_OF_SCOPE_SERVICE_ACCOUNT.name
    assert error["field"] == "id"
    assert AppToken.objects.filter(id=token.id).exists()
