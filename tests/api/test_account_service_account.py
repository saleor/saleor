import graphene
import pytest
from freezegun import freeze_time

from saleor.app.models import App, AppToken
from saleor.graphql.core.enums import PermissionEnum

from .utils import assert_no_permission, get_graphql_content

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
            errors{
                field
                message
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
    staff_user.user_permissions.add(permission_manage_service_accounts)

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    service_account_data = content["data"]["serviceAccountCreate"]["serviceAccount"]
    default_token = content["data"]["serviceAccountCreate"]["authToken"]
    service_account = App.objects.get()
    assert service_account_data["isActive"] == service_account.is_active
    assert service_account_data["name"] == service_account.name
    assert list(service_account.permissions.all()) == [permission_manage_products]
    assert default_token == service_account.tokens.get().auth_token


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
        errors{
            field
            message
        }
    }
}
"""


def test_service_account_update_mutation(
    app,
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    staff_user.user_permissions.add(permission_manage_service_accounts)
    id = graphene.Node.to_global_id("ServiceAccount", app.id)

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
    second_service_account = App.objects.create(name="Simple service")
    second_service_account.is_active = False
    second_service_account.tokens.create(name="default")
    second_service_account.save()

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
    errors{
      field
      message
    }
  }
}
"""


def test_service_account_token_create(
    permission_manage_service_accounts, staff_api_client, staff_user
):

    service_account = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_service_accounts)

    id = graphene.Node.to_global_id("ServiceAccount", service_account.id)
    variables = {"name": "Default token", "serviceAccount": id}
    response = staff_api_client.post_graphql(query, variables={"input": variables})
    content = get_graphql_content(response)
    token_data = content["data"]["serviceAccountTokenCreate"]["serviceAccountToken"]
    auth_token_data = content["data"]["serviceAccountTokenCreate"]["authToken"]
    auth_token = service_account.tokens.get().auth_token
    assert auth_token_data == auth_token

    assert token_data["authToken"] == auth_token[-4:]
    assert token_data["name"] == "Default token"


def test_service_account_token_create_no_permissions(staff_api_client, staff_user):
    service_account = App.objects.create(name="New_sa")
    query = SERVICE_ACCOUNT_TOKEN_CREATE_MUTATION
    id = graphene.Node.to_global_id("ServiceAccount", service_account.id)
    variables = {"name": "Default token", "serviceAccount": id}
    response = staff_api_client.post_graphql(query, variables={"input": variables})
    assert_no_permission(response)


SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION = """
    mutation serviceAccountTokenDelete($id: ID!){
      serviceAccountTokenDelete(id: $id){
        errors{
          field
          message
        }
        serviceAccountToken{
          name
          authToken
        }
      }
    }
"""


def test_service_account_token_delete(
    permission_manage_service_accounts, staff_api_client, staff_user, app
):

    query = SERVICE_ACCOUNT_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    id = graphene.Node.to_global_id("ServiceAccountToken", token.id)
    staff_user.user_permissions.add(permission_manage_service_accounts)

    variables = {"id": id}
    response = staff_api_client.post_graphql(query, variables=variables)
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
