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

    assert errors == []
    assert permission_group_data["name"] == group.name
    permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert set(group.permissions.all().values_list("name", flat=True)) == permissions


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
    mutation PermissionGroupAssignUsers($id: ID!, $users: [ID!]!) {
        permissionGroupAssignUsers(
            id: $id, users: $users)
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
        "users": users,
    }

    staff_members += list(group.user_set.all())

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
        "users": users,
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
        "users": [],
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


def test_permission_group_assign_users_mutation_customer_user(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    customer_user,
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_ASSIGN_USERS_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "users": [graphene.Node.to_global_id("User", customer_user.id)],
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupAssignUsers"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "users"
    assert errors[0]["message"] == "Some of users aren't staff members."
    assert data["group"] is None


PERMISSION_GROUP_UNASSIGN_USERS_MUTATION = """
    mutation PermissionGroupUnassignUsers($id: ID!, $users: [ID!]!) {
        permissionGroupUnassignUsers(
            id: $id, users: $users)
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


def test_permission_group_unassign_users_mutation(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    group_name = group.name
    query = PERMISSION_GROUP_UNASSIGN_USERS_MUTATION

    staff_user2 = group.user_set.first()
    group.user_set.add(staff_user)

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "users": [graphene.Node.to_global_id("User", staff_user2.id)],
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUnassignUsers"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert errors == []
    assert permission_group_data["name"] == group_name
    assert permission_group_data["users"]
    user_emails = {user_data["email"] for user_data in permission_group_data["users"]}
    assert user_emails == {staff_user.email}
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


def test_permission_group_unassign_users_mutation_no_permission_to_perform_mutation(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UNASSIGN_USERS_MUTATION

    group_staff_user = group.user_set.first()

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "users": [graphene.Node.to_global_id("User", group_staff_user.id)],
    }

    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_permission_group_unassign_users_mutation_no_users_data(
    permission_group_manage_users, staff_user, permission_manage_staff, staff_api_client
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UNASSIGN_USERS_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "users": [],
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUnassignUsers"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "users"
    assert errors[0]["message"] == "You must provide at least one staff user."
    assert data["group"] is None


def test_permission_group_unassign_users_mutation_user_not_in_group(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    customer_user,
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UNASSIGN_USERS_MUTATION

    group_staff_user = group.user_set.first()

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "users": [graphene.Node.to_global_id("User", customer_user.id)],
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUnassignUsers"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert errors == []
    assert permission_group_data["name"] == group.name
    assert permission_group_data["users"]
    user_emails = {user_data["email"] for user_data in permission_group_data["users"]}
    assert user_emails == {group_staff_user.email}
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


QUERY_PERMISSION_GROUP_WITH_FILTER = """
    query ($filter: PermissionGroupFilterInput ){
        permissionGroups(first: 5, filter: $filter){
            edges{
                node{
                    id
                    name
                    permissions{
                        name
                        code
                    }
                    users {
                        email
                    }
                }
            }
        }
    }
    """


@pytest.mark.parametrize(
    "permission_group_filter, count",
    (({"search": "Manage user groups"}, 1), ({"search": "Manage"}, 2), ({}, 3)),
)
def test_permission_groups_query(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_filter,
    count,
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP_WITH_FILTER

    group2 = Group.objects.get(pk=group.pk)
    group2.id = None
    group2.name = "Manage product."
    group2.save()

    group3 = Group.objects.get(pk=group.pk)
    group3.id = None
    group3.name = "Remove product."
    group3.save()

    variables = {"filter": permission_group_filter}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroups"]["edges"]

    assert len(data) == count


def test_permission_groups_no_permission_to_perform(
    permission_group_manage_users, permission_manage_staff, staff_api_client,
):
    query = QUERY_PERMISSION_GROUP_WITH_FILTER

    variables = {"filter": {"search": "Manage user groups"}}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


QUERY_PERMISSION_GROUP_WITH_SORT = """
    query ($sort_by: PermissionGroupSortingInput!) {
        permissionGroups(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "permission_group_sort, result",
    (
        (
            {"field": "NAME", "direction": "ASC"},
            ["Add", "Manage user groups.", "Remove"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["Remove", "Manage user groups.", "Add"],
        ),
    ),
)
def test_permission_group_with_sort(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_sort,
    result,
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP_WITH_SORT

    group2 = Group.objects.get(pk=group.pk)
    group2.id = None
    group2.name = "Add"
    group2.save()

    group3 = Group.objects.get(pk=group.pk)
    group3.id = None
    group3.name = "Remove"
    group3.save()

    variables = {"sort_by": permission_group_sort}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroups"]["edges"]

    for order, group_name in enumerate(result):
        assert data[order]["node"]["name"] == group_name


QUERY_PERMISSION_GROUP = """
    query ($id: ID! ){
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
        }
    }
    """


def test_permission_group_query(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP

    group_staff_user = group.user_set.first()

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroup"]

    assert data["name"] == group.name
    assert len(data["users"]) == 1
    assert data["users"][0]["email"] == group_staff_user.email
    result_permissions = {permission["name"] for permission in data["permissions"]}
    assert (
        set(group.permissions.all().values_list("name", flat=True))
        == result_permissions
    )
    permissions_codes = {
        permission["code"].lower() for permission in data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )


def test_permission_group_no_permission_to_perform(
    permission_group_manage_users, permission_manage_staff, staff_api_client,
):
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
