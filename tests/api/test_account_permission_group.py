from django.contrib.auth.models import Group

from saleor.core.permissions import AccountPermissions

from .utils import assert_no_permission, get_graphql_content

PERMISSION_GROUP_CREATE_MUTATION = """
    mutation PermissionGroupCreate(
        $name: String!, $permissions: [PermissionEnum!]) {
        permissionGroupCreate(
            input: {name: $name, permissions: $permissions})
        {
            group{
                name
                permissions {
                    name
                }
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
        "name": "New permission group",
        "permissions": [
            AccountPermissions.MANAGE_USERS.name,
            AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
        ],
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    permission_group_data = content["data"]["permissionGroupCreate"]["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name
    permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert set(group.permissions.all().values_list("name", flat=True)) == permissions


def test_permission_group_create_mutation_no_permission_to_perform_mutation(
    staff_user, staff_api_client
):
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "name": "New permission group",
        "permissions": [
            AccountPermissions.MANAGE_USERS.name,
            AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
        ],
    }
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_permission_group_create_mutation_group_exists(
    staff_user, permission_manage_staff, staff_api_client, permission_group_manage_users
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "name": permission_group_manage_users.name,
        "permissions": [
            AccountPermissions.MANAGE_USERS.name,
            AccountPermissions.MANAGE_SERVICE_ACCOUNTS.name,
        ],
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["permissionGroupCreate"]["group"] is None


PERMISSION_GROUP_CREATE_MUTATION = """
    mutation PermissionGroupCreate(
        $name: String!) {
        permissionGroupCreate(
            input: {name: $name})
        {
            group{
                name
                permissions {
                    name
                }
            }
        }
    }
    """


def test_permission_group_create_mutation_no_permissions_data(
    staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "name": "New permission group",
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    permission_group_data = content["data"]["permissionGroupCreate"]["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name
    assert not group.permissions.all()
