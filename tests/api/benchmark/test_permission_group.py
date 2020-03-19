import graphene
import pytest
from django.contrib.auth.models import Group

from saleor.core.permissions import AccountPermissions
from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_permission_group_create(
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_service_accounts,
    count_queries,
):
    staff_user.user_permissions.add(
        permission_manage_users, permission_manage_service_accounts
    )
    query = """
        mutation PermissionGroupCreate(
        $input: PermissionGroupCreateInput!) {
        permissionGroupCreate(
            input: $input)
        {
            group{
                id
                name
                permissions {
                    name
                    code
                }
            }
            bulkAccountErrors{
                field
                code
                index
                message
            }
        }
    }
    """

    group_count = Group.objects.count()

    variables = {
        "input": {
            "name": "New permission group",
            "permissions": [
                AccountPermissions.MANAGE_USERS.name,
                AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
            ],
        }
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]

    groups = Group.objects.all()
    assert data["bulkAccountErrors"] == []
    assert len(groups) == group_count + 1


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_permission_group_update(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_service_accounts,
    permission_manage_users,
    count_queries,
):
    staff_user.user_permissions.add(
        permission_manage_users, permission_manage_service_accounts
    )
    query = """
    mutation PermissionGroupUpdate(
        $id: ID!, $input: PermissionGroupUpdateInput!) {
        permissionGroupUpdate(
            id: $id, input: $input)
        {
            group{
                id
                name
                permissions {
                    name
                    code
                }
            }
            bulkAccountErrors{
                field
                code
                index
                message
            }
        }
    }
    """

    group_count = Group.objects.count()

    staff_user.user_permissions.add(
        permission_manage_service_accounts, permission_manage_users
    )
    group = permission_group_manage_users

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "permissions": [AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]

    groups = Group.objects.all()
    assert data["bulkAccountErrors"] == []
    assert len(groups) == group_count


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_permission_group_query(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    permission_manage_users,
    staff_api_client,
    count_queries,
):
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    group = permission_group_manage_users
    query = """
    query ($id: ID!){
        permissionGroup(id: $id){
            id
            name
            permissions {
                name
                code
            }
            users{
                email
            }
            userCanManage
        }
    }
    """

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroup"]
    assert data
