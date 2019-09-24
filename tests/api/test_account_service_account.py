import graphene
import pytest

from saleor.account.models import ServiceAccount
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
                authToken
                permissions{
                    code
                    name
                }
                id
                isActive
                name
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
    auth_token = content["data"]["serviceAccountCreate"]["authToken"]
    service_account = ServiceAccount.objects.get()
    assert auth_token == service_account.auth_token
    assert service_account_data["isActive"] == service_account.is_active
    assert service_account_data["name"] == service_account.name
    assert list(service_account.permissions.all()) == [permission_manage_products]


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
            authToken
            permissions{
                code
                name
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
    service_account,
    permission_manage_service_accounts,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    staff_user.user_permissions.add(permission_manage_service_accounts)
    id = graphene.Node.to_global_id("ServiceAccount", service_account.id)

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
    service_account.refresh_from_db()

    assert service_account_data["isActive"] == service_account.is_active
    assert service_account.is_active is False
    assert service_account_data["authToken"] == service_account.auth_token[-4:]
    assert set(service_account.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_service_account_update_no_permission(
    service_account, staff_api_client, staff_user
):
    query = SERVICE_ACCOUNT_UPDATE_MUTATION
    id = graphene.Node.to_global_id("ServiceAccount", service_account.id)
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
                    authToken
                    isActive
                    permissions{
                        name
                        code
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
    service_account,
    service_account_filter,
    count,
):
    second_service_account = ServiceAccount.objects.create(name="Simple service")
    second_service_account.is_active = False
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
        token = service_account_data["node"]["authToken"]
        assert len(token) == 4
    assert len(service_accounts_data) == count


def test_service_accounts_query_no_permission(
    staff_api_client, permission_manage_users, permission_manage_staff, service_account
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
            authToken
            created
            isActive
            permissions{
                code
                name
            }
            name
        }
    }
    """


def test_service_account_query(
    staff_api_client,
    permission_manage_service_accounts,
    permission_manage_staff,
    service_account,
):
    service_account.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("ServiceAccount", service_account.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT,
        variables,
        permissions=[permission_manage_service_accounts],
    )
    content = get_graphql_content(response)

    service_account_data = content["data"]["serviceAccount"]
    assert service_account_data["authToken"] == service_account.auth_token[-4:]
    assert service_account_data["isActive"] == service_account.is_active
    assert service_account_data["permissions"] == [
        {"code": "MANAGE_STAFF", "name": "Manage staff."}
    ]


def test_service_account_query_no_permission(
    staff_api_client, permission_manage_staff, permission_manage_users, service_account
):
    service_account.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("ServiceAccount", service_account.id)
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
    service_account_api_client,
    service_account,
    permission_manage_orders,
    order_with_lines,
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
    response = service_account_api_client.post_graphql(query)
    assert_no_permission(response)
    service_account.permissions.add(permission_manage_orders)
    response = service_account_api_client.post_graphql(query)
    get_graphql_content(response)
