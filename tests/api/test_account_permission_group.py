import graphene
import pytest
from django.contrib.auth.models import Group

from saleor.core.permissions import AccountPermissions

from .utils import assert_no_permission, get_graphql_content

PERMISSION_GROUP_CREATE_MUTATION = """
    mutation PermissionGroupCreate(
        $input: PermissionGroupCreateInput!) {
        permissionGroupCreate(
            input: $input)
        {
            group{
                name
                permissions {
                    name
                }
            }
            errors{
                field
                message
            }
        }
    }
    """


def test_permission_group_create_mutation(
    staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "permissions": [
                AccountPermissions.MANAGE_USERS.name,
                AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
            ],
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name
    permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert set(group.permissions.all().values_list("name", flat=True)) == permissions
    assert data["errors"] == []


def test_permission_group_create_mutation_no_permission_to_perform_mutation(
    staff_user, staff_api_client
):
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "permissions": [
                AccountPermissions.MANAGE_USERS.name,
                AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
            ],
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_permission_group_create_mutation_group_exists(
    staff_user, permission_manage_staff, staff_api_client, permission_group_manage_users
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": permission_group_manage_users.name,
            "permissions": [
                AccountPermissions.MANAGE_USERS.name,
                AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
            ],
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert permission_group_data is None
    assert len(errors) == 1
    assert errors[0]["field"] == "name"
    assert errors[0]["message"] == "Group with this Name already exists."


def test_permission_group_create_mutation_no_permissions_data(
    staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {"input": {"name": "New permission group"}}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name
    assert not group.permissions.all()
    assert data["errors"] == []


def test_permission_group_create_mutation_no_name(
    staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": None,
            "permissions": [
                AccountPermissions.MANAGE_USERS.name,
                AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
            ],
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    with pytest.raises(AssertionError):
        get_graphql_content(response)


PERMISSION_GROUP_UPDATE_MUTATION = """
    mutation PermissionGroupUpdate(
        $id: ID!, $input: PermissionGroupInput!) {
        permissionGroupUpdate(
            id: $id, input: $input)
        {
            group{
                name
                permissions {
                    name
                }
            }
            errors{
                field
                message
            }
        }
    }
    """


def test_permission_group_update_mutation(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "permissions": [AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name],
        },
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name
    permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert set(group.permissions.all().values_list("name", flat=True)) == permissions
    assert data["errors"] == []


def test_permission_group_update_mutation_only_name(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    old_group_name = group.name
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"name": "New permission group"},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert group.name != old_group_name
    assert permission_group_data["name"] == group.name
    assert group.permissions.all().count() == 1
    assert group.permissions.first() == permission_manage_users
    result_permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("name", flat=True))
        == result_permissions
    )
    assert data["errors"] == []


def test_permission_group_update_mutation_only_permissions(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    old_group_name = group.name
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"permissions": [AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name]},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert group.name == old_group_name
    assert permission_group_data["name"] == group.name
    permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert set(group.permissions.all().values_list("name", flat=True)) == permissions
    assert data["errors"] == []


def test_permission_group_update_mutation_no_permission_to_perform_mutation(
    permission_group_manage_users, staff_user, staff_api_client
):
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "permissions": [AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name],
        },
    }
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_permission_group_update_mutation_no_input_data(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group.id), "input": {}}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert permission_group_data is None
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["message"] == "You must provide name or permissions to update."
