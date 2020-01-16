import graphene
import pytest
from django.contrib.auth.models import Group

from saleor.account.models import User
from saleor.core.permissions import AccountPermissions

from .utils import assert_no_permission, get_graphql_content

PERMISSION_GROUP_CREATE_MUTATION = """
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
    permissions_codes = {
        permission["code"].lower()
        for permission in permission_group_data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
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
                id
                name
                permissions {
                    name
                    code
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
    permissions_codes = {
        permission["code"].lower()
        for permission in permission_group_data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
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
    permissions_codes = {
        permission["code"].lower()
        for permission in permission_group_data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
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


PERMISSION_GROUP_DELETE_MUTATION = """
    mutation PermissionGroupDelete($id: ID!) {
        permissionGroupDelete(
            id: $id)
        {
            group{
                id
                name
                permissions {
                    name
                    code
                }
            }
            errors{
                field
                message
            }
        }
    }
    """


def test_group_delete_mutation(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    group_name = group.name
    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert errors == []
    assert permission_group_data["id"] == variables["id"]
    assert permission_group_data["name"] == group_name
    assert permission_group_data["permissions"] == []


def test_group_delete_mutation_no_id(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": None}
    response = staff_api_client.post_graphql(query, variables)
    with pytest.raises(AssertionError):
        get_graphql_content(response)


PERMISSION_GROUP_ASSIGN_USERS_MUTATION = """
    mutation PermissionGroupAssignUsers($id: ID!, $input: AssignUsersInput!) {
        permissionGroupAssignUsers(
            id: $id, input: $input)
        {
            group{
                id
                name
                permissions {
                    name
                    code
                }
                users{
                    email
                }
            }
            errors{
                field
                message
            }
        }
    }
    """


def test_permission_group_assign_users_mutation(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    group_name = group.name
    query = PERMISSION_GROUP_ASSIGN_USERS_MUTATION

    staff_user2 = User.objects.get(pk=staff_user.pk)
    staff_user2.id = None
    staff_user2.email = "test@example.com"
    staff_user2.save()
    staff_user2.refresh_from_db()

    staff_members = [staff_user, staff_user2]
    users = [graphene.Node.to_global_id("User", user.id) for user in staff_members]

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"users": users},
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupAssignUsers"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert errors == []
    assert permission_group_data["name"] == group_name
    assert permission_group_data["users"]
    user_emails = {user_data["email"] for user_data in permission_group_data["users"]}
    assert user_emails == {user.email for user in staff_members}
    assert permission_group_data["permissions"]
    result_permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("name", flat=True))
        == result_permissions
    )
    permissions_codes = {
        permission["code"].lower()
        for permission in permission_group_data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )


def test_permission_group_assign_users_mutation_no_permission_to_perform_mutation(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    group = permission_group_manage_users
    query = PERMISSION_GROUP_ASSIGN_USERS_MUTATION

    staff_user2 = User.objects.get(pk=staff_user.pk)
    staff_user2.id = None
    staff_user2.email = "test@example.com"
    staff_user2.save()
    staff_user2.refresh_from_db()

    users = [
        graphene.Node.to_global_id("User", user.id)
        for user in [staff_user, staff_user2]
    ]

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"users": users},
    }

    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_permission_group_assign_users_mutation_no_users_data(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_ASSIGN_USERS_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"users": []},
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupAssignUsers"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "users"
    assert errors[0]["message"] == "You must provide at least one staff user."
    assert data["group"] is None
