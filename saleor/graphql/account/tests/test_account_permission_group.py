import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ....account.error_codes import PermissionGroupErrorCode
from ....account.models import Group, User
from ....core.utils.json_serializer import CustomJsonEncoder
from ....permission.enums import AccountPermissions, AppPermission, OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import generate_meta, generate_requestor
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

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
                users {
                    email
                }
            }
            errors{
                field
                code
                permissions
                users
                message
            }
        }
    }
    """


def test_permission_group_create_mutation(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
            "addUsers": [
                graphene.Node.to_global_id("User", user.id) for user in staff_users
            ],
        }
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name == variables["input"]["name"]
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
        == set(perm.lower() for perm in variables["input"]["addPermissions"])
    )
    assert (
        {user["email"] for user in permission_group_data["users"]}
        == {user.email for user in staff_users}
        == set(group.user_set.all().values_list("email", flat=True))
    )
    assert data["errors"] == []


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_permission_group_create_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
            "addUsers": [
                graphene.Node.to_global_id("User", user.id) for user in staff_users
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    group = Group.objects.last()

    # then
    assert not data["errors"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Group", group.id),
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.PERMISSION_GROUP_CREATED,
        [any_webhook],
        group,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_permission_group_create_app_no_permission(
    staff_users,
    permission_manage_staff,
    app_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
            "addUsers": [
                graphene.Node.to_global_id("User", user.id) for user in staff_users
            ],
        }
    }
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )

    assert_no_permission(response)


def test_permission_group_create_mutation_only_required_fields(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {"input": {"name": "New permission group"}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name == variables["input"]["name"]
    assert permission_group_data["permissions"] == []
    assert not group.permissions.all()
    assert permission_group_data["users"] == []
    assert not group.user_set.all()


def test_permission_group_create_mutation_only_required_fields_not_none(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "addUsers": None,
            "addPermissions": None,
        }
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]

    group = Group.objects.get()
    assert permission_group_data["name"] == group.name == variables["input"]["name"]
    assert permission_group_data["permissions"] == []
    assert not group.permissions.all()
    assert permission_group_data["users"] == []
    assert not group.user_set.all()


def test_permission_group_create_mutation_lack_of_permission(
    staff_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_manage_orders,
):
    """Ensue staff user can't create group with wider scope of permissions.
    Ensure that superuser pass restrictions.
    """
    staff_user.user_permissions.add(permission_manage_orders)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                OrderPermissions.MANAGE_ORDERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
        }
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "addPermissions"
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert set(errors[0]["permissions"]) == {
        AccountPermissions.MANAGE_USERS.name,
        AppPermission.MANAGE_APPS.name,
    }
    assert errors[0]["users"] is None

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert not errors
    group = Group.objects.get()
    assert data["group"]["name"] == group.name == variables["input"]["name"]
    permissions_codes = {
        permission["code"].lower() for permission in data["group"]["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
        == set(perm.lower() for perm in variables["input"]["addPermissions"])
    )


def test_permission_group_create_mutation_group_exists(
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_apps,
):
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": permission_group_manage_users.name,
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
            "addUsers": [graphene.Node.to_global_id("User", staff_user.id)],
        }
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert permission_group_data is None
    assert len(errors) == 1
    assert errors[0]["field"] == "name"
    assert errors[0]["code"] == PermissionGroupErrorCode.UNIQUE.name
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] is None


def test_permission_group_create_mutation_add_customer_user(
    staff_user,
    customer_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    """Ensure creating permission group with customer user in input field for adding
    users failed. Mutations should failed. Error should contains list of wrong users
    IDs.
    Ensure this mutation also fail for superuser.
    """

    second_customer = User.objects.create(
        email="second_customer@test.com", password="test"
    )

    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    user_ids = [
        graphene.Node.to_global_id("User", user.id)
        for user in [staff_user, customer_user, second_customer]
    ]
    variables = {
        "input": {
            "name": "New permission group",
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
            "addUsers": user_ids,
        }
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "addUsers"
    assert errors[0]["permissions"] is None
    assert set(errors[0]["users"]) == set(user_ids[1:])
    assert errors[0]["code"] == PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.name
    assert data["group"] is None

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "addUsers"
    assert errors[0]["permissions"] is None
    assert set(errors[0]["users"]) == set(user_ids[1:])
    assert errors[0]["code"] == PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.name
    assert data["group"] is None


def test_permission_group_create_mutation_lack_of_permission_and_customer_user(
    staff_user,
    customer_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    staff_user.user_permissions.add(permission_manage_users)
    query = PERMISSION_GROUP_CREATE_MUTATION

    user_ids = [
        graphene.Node.to_global_id("User", user.id)
        for user in [staff_user, customer_user]
    ]
    variables = {
        "input": {
            "name": "New permission group",
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
            "addUsers": user_ids,
        }
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 2
    assert {error["field"] for error in errors} == {"addUsers", "addPermissions"}
    assert [AppPermission.MANAGE_APPS.name] in [
        error["permissions"] for error in errors
    ]
    assert user_ids[1:] in [error["users"] for error in errors]
    assert {error["code"] for error in errors} == {
        PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.name,
        PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.name,
    }
    assert data["group"] is None


def test_permission_group_create_mutation_requestor_does_not_have_all_users_perms(
    staff_users,
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    """Ensure user can create group with user whose permission scope
    is wider than requestor scope.
    """

    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_apps)
    permission_group_manage_users.user_set.add(staff_users[1])
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "addUsers": [
                graphene.Node.to_global_id("User", user.id) for user in staff_users
            ],
        }
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert not errors
    group_name = variables["input"]["name"]
    group = Group.objects.get(name=group_name)
    assert data["group"]["name"] == group.name == group_name
    permissions_codes = {
        permission["code"].lower() for permission in data["group"]["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
        == set(perm.lower() for perm in variables["input"]["addPermissions"])
    )
    assert (
        {user["email"] for user in data["group"]["users"]}
        == {user.email for user in staff_users}
        == set(group.user_set.all().values_list("email", flat=True))
    )


PERMISSION_GROUP_UPDATE_MUTATION = """
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
                users {
                    email
                }
            }
            errors{
                field
                code
                permissions
                users
                message
            }
        }
    }
    """


def test_permission_group_update_mutation(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_apps,
    permission_manage_users,
):
    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_users)
    query = PERMISSION_GROUP_UPDATE_MUTATION

    group1, group2 = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_users, permission_manage_staff)

    group1_user = staff_users[1]
    group1.user_set.add(group1_user)
    group2.user_set.add(staff_user)

    # set of users emails being in a group
    users = set(group1.user_set.values_list("email", flat=True))

    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "removePermissions": [AccountPermissions.MANAGE_USERS.name],
            "addUsers": [graphene.Node.to_global_id("User", staff_user.pk)],
            "removeUsers": [graphene.Node.to_global_id("User", group1_user.pk)],
        },
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]

    # remove and add user email for comparing users set
    users.remove(group1_user.email)
    users.add(staff_user.email)

    group1.refresh_from_db()
    assert permission_group_data["name"] == group1.name
    permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert set(group1.permissions.all().values_list("name", flat=True)) == permissions
    permissions_codes = {
        permission["code"].lower()
        for permission in permission_group_data["permissions"]
    }
    assert (
        set(group1.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
    assert set(group1.user_set.all().values_list("email", flat=True)) == users
    assert data["errors"] == []


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_permission_group_update_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_apps,
    permission_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_users)
    query = PERMISSION_GROUP_UPDATE_MUTATION

    group1, group2 = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_users, permission_manage_staff)

    group1_user = staff_users[1]
    group1.user_set.add(group1_user)
    group2.user_set.add(staff_user)

    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "removePermissions": [AccountPermissions.MANAGE_USERS.name],
            "addUsers": [graphene.Node.to_global_id("User", staff_user.pk)],
            "removeUsers": [graphene.Node.to_global_id("User", group1_user.pk)],
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    group1.refresh_from_db()

    # then
    assert not data["errors"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Group", group1.id),
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.PERMISSION_GROUP_UPDATED,
        [any_webhook],
        group1,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_permission_group_update_mutation_removing_perm_left_not_manageable_perms(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_apps,
    permission_manage_users,
):
    """Ensure user cannot remove permissions if it left not meanagable perms."""
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_users)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    group_user = group.user_set.first()
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "removePermissions": [AccountPermissions.MANAGE_USERS.name],
            "addUsers": [graphene.Node.to_global_id("User", staff_user.pk)],
            "removeUsers": [graphene.Node.to_global_id("User", group_user.pk)],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removePermissions"
    assert (
        errors[0]["code"]
        == PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    )
    assert errors[0]["permissions"] == [AccountPermissions.MANAGE_USERS.name]
    assert errors[0]["users"] is None
    assert staff_user.groups.count() == 0


def test_permission_group_update_mutation_superuser_can_remove_any_perms(
    permission_group_manage_users,
    permission_manage_staff,
    superuser_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_users,
):
    """Ensure superuser can remove any permissions."""
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    # set of users emails being in a group
    users = set(group.user_set.values_list("email", flat=True))

    group_user = group.user_set.first()
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "removePermissions": [AccountPermissions.MANAGE_USERS.name],
            "addUsers": [graphene.Node.to_global_id("User", staff_user.pk)],
            "removeUsers": [graphene.Node.to_global_id("User", group_user.pk)],
        },
    }
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]

    # remove and add user email for comparing users set
    users.remove(group_user.email)
    users.add(staff_user.email)

    group.refresh_from_db()
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
    assert set(group.user_set.all().values_list("email", flat=True)) == users
    assert data["errors"] == []


def test_permission_group_update_mutation_app_no_permission(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    app_api_client,
    permission_manage_apps,
    permission_manage_users,
):
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_users)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    group_user = group.user_set.first()
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "removePermissions": [AccountPermissions.MANAGE_USERS.name],
            "addUsers": [graphene.Node.to_global_id("User", staff_user.pk)],
            "removeUsers": [graphene.Node.to_global_id("User", group_user.pk)],
        },
    }
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )

    assert_no_permission(response)


def test_permission_group_update_mutation_remove_me_from_last_group(
    permission_group_manage_users,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    """Ensure mutation failed when user removing himself from user's last group."""
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(permission_manage_users)
    group = permission_group_manage_users
    group.permissions.add(permission_manage_staff)
    # ensure user is in group
    group.user_set.add(staff_user, staff_user1)
    assert staff_user.groups.count() == 1

    query = PERMISSION_GROUP_UPDATE_MUTATION

    staff_user_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"removeUsers": [staff_user_id]},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]
    errors = data["errors"]

    assert not permission_group_data
    assert len(errors) == 1
    assert errors[0]["field"] == "removeUsers"
    assert (
        errors[0]["code"] == PermissionGroupErrorCode.CANNOT_REMOVE_FROM_LAST_GROUP.name
    )
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] == [staff_user_id]
    assert staff_user.groups.count() == 1


def test_permission_group_update_mutation_remove_me_from_not_last_group(
    permission_group_manage_users,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_orders,
):
    """Ensure user can remove himself from group if he is a member of another group."""
    staff_user, staff_user1, _ = staff_users
    staff_user.user_permissions.add(permission_manage_users)
    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_users, permission_manage_staff)

    # ensure user is in group
    group1.user_set.add(staff_user)
    group2.user_set.add(staff_user, staff_user1)

    assert staff_user.groups.count() == 2

    query = PERMISSION_GROUP_UPDATE_MUTATION

    staff_user_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {"removeUsers": [staff_user_id]},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]
    errors = data["errors"]

    assert not errors
    assert staff_user_id not in permission_group_data["users"]
    assert staff_user.groups.count() == 1


def test_permission_group_update_mutation_remove_last_user_from_group(
    permission_group_manage_users,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    """Ensure user can remove last user from the group."""
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(permission_manage_users)
    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups
    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_users, permission_manage_staff)

    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)

    # ensure group contains only 1 user
    assert group1.user_set.count() == 1

    group_user = group1.user_set.first()

    query = PERMISSION_GROUP_UPDATE_MUTATION

    group_user_id = graphene.Node.to_global_id("User", group_user.pk)
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {"removeUsers": [group_user_id]},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]
    errors = data["errors"]

    assert not errors
    assert staff_user.groups.count() == 0
    assert permission_group_data["users"] == []


def test_permission_group_update_mutation_only_name(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    """Ensure mutation update group when only name are passed in input."""
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
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


def test_permission_group_update_mutation_only_name_other_fields_with_none(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    """Ensure mutation update group when only name are passed in input."""
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    group = permission_group_manage_users
    old_group_name = group.name
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": None,
            "removePermissions": None,
            "addUsers": None,
            "removeUsers": None,
        },
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


def test_permission_group_update_mutation_with_name_which_exists(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    """Ensure mutation failed where updating name with value which already is a name of
    different group.
    """
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    group = permission_group_manage_users
    old_group_name = group.name
    query = PERMISSION_GROUP_UPDATE_MUTATION

    new_name = "New permission group"
    Group.objects.create(name=new_name)

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"name": new_name},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]
    errors = data["errors"]

    group.refresh_from_db()
    assert not permission_group_data
    assert len(errors) == 1
    assert errors[0]["field"] == "name"
    assert errors[0]["code"] == PermissionGroupErrorCode.UNIQUE.name
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] is None
    assert group.name == old_group_name


def test_permission_group_update_mutation_only_permissions(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    """Ensure mutation update group when only permissions are passed in input."""
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    group = permission_group_manage_users
    old_group_name = group.name
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"addPermissions": [AppPermission.MANAGE_APPS.name]},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
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


def test_permission_group_update_mutation_no_input_data(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    permission_manage_users,
    staff_api_client,
):
    """Ensure mutation doesn't change group when input is empty."""
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
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


def test_permission_group_update_mutation_user_cannot_manage_group(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_manage_apps,
):
    """Ensure that update mutation failed when user try to update group for which
    he doesn't have permission.
    Ensure superuser pass restrictions.
    """
    staff_user.user_permissions.add(permission_manage_apps)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
        },
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert errors[0]["field"] is None

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    group_name = variables["input"]["name"]
    group = Group.objects.get(name=group_name)
    assert not errors
    assert data["group"]["name"] == group_name == group.name
    permissions_codes = {
        permission["code"].lower() for permission in data["group"]["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
    assert variables["input"]["addPermissions"][0].lower() in permissions_codes


def test_permission_group_update_mutation_user_in_list_to_add_and_remove(
    permission_group_manage_users,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
):
    """Ensure update mutation failed when user IDs are in both lists for adding
    and removing. Ensure mutation contains list of user IDs which cause
    the problem.
    """
    staff_user = staff_users[0]
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    staff_user2_id = graphene.Node.to_global_id("User", staff_users[1].pk)

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addUsers": [
                graphene.Node.to_global_id("User", user.pk) for user in staff_users
            ],
            "removeUsers": [staff_user2_id],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "users"
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] == [staff_user2_id]


def test_permission_group_update_mutation_permissions_in_list_to_add_and_remove(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure update mutation failed when permission items are in both lists for
    adding and removing. Ensure mutation contains list of permissions which cause
    the problem.
    """
    staff_user.user_permissions.add(
        permission_manage_users,
        permission_manage_apps,
        permission_manage_orders,
    )
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    permissions = [
        OrderPermissions.MANAGE_ORDERS.name,
        AppPermission.MANAGE_APPS.name,
    ]
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": permissions,
            "removePermissions": permissions,
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "permissions"
    assert set(errors[0]["permissions"]) == set(permissions)
    assert errors[0]["users"] is None


def test_permission_group_update_mutation_permissions_and_users_duplicated(
    permission_group_manage_users,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure updating mutations with the same permission and users in list for
    adding and removing failed. Mutation should failed. Error should contains list of
    users IDs and permissions that are duplicated.
    """
    staff_user = staff_users[0]
    staff_user.user_permissions.add(
        permission_manage_users,
        permission_manage_apps,
        permission_manage_orders,
    )
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    staff_user2_id = graphene.Node.to_global_id("User", staff_users[1].pk)

    permissions = [
        OrderPermissions.MANAGE_ORDERS.name,
        AppPermission.MANAGE_APPS.name,
    ]
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": permissions,
            "removePermissions": permissions,
            "addUsers": [
                graphene.Node.to_global_id("User", user.pk) for user in staff_users
            ],
            "removeUsers": [staff_user2_id],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 2
    assert {error["code"] for error in errors} == {
        PermissionGroupErrorCode.DUPLICATED_INPUT_ITEM.name
    }
    assert {error["field"] for error in errors} == {"users", "permissions"}
    assert set(permissions) in [
        set(error["permissions"]) if error["permissions"] else None for error in errors
    ]
    assert [staff_user2_id] in [error["users"] for error in errors]


def test_permission_group_update_mutation_user_add_customer_user(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_manage_users,
    permission_manage_apps,
    customer_user,
):
    """Ensure update mutation with customer user in field for adding users failed.
    Ensure error contains list with user IDs which cause the problem.
    Ensure it also fail for superuser.
    """
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addUsers": [
                graphene.Node.to_global_id("User", user.pk)
                for user in [staff_user, customer_user]
            ],
        },
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.name
    assert errors[0]["field"] == "addUsers"
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] == [customer_user_id]

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.name
    assert errors[0]["field"] == "addUsers"
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] == [customer_user_id]


def test_permission_group_update_mutation_lack_of_permission(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_manage_users,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure update mutation failed when user trying to add permission which
    he doesn't have.
    Ensure superuser pass the restrictions.
    """
    staff_user.user_permissions.add(permission_manage_users, permission_manage_apps)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    permissions = [
        OrderPermissions.MANAGE_ORDERS.name,
        AppPermission.MANAGE_APPS.name,
    ]
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"name": "New permission group", "addPermissions": permissions},
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert errors[0]["field"] == "addPermissions"
    assert errors[0]["permissions"] == [OrderPermissions.MANAGE_ORDERS.name]
    assert errors[0]["users"] is None

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not errors
    group_name = variables["input"]["name"]
    group = Group.objects.get(name=group_name)
    assert not errors
    assert data["group"]["name"] == group_name == group.name
    permissions_codes = {
        permission["code"].lower() for permission in data["group"]["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
    for perm in permissions:
        assert perm.lower() in permissions_codes


def test_permission_group_update_mutation_out_of_scope_users(
    staff_users,
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_manage_users,
    permission_manage_apps,
    permission_manage_orders,
    permission_manage_products,
):
    """Ensure user can assign and cannot unasign users whose permission scope
    is wider than requestor scope.
    Ensure superuser pass restrictions.
    """

    staff_user = staff_users[0]
    staff_user3 = User.objects.create_user(
        email="staff3_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    staff_user.user_permissions.add(permission_manage_apps, permission_manage_users)
    staff_users[1].user_permissions.add(permission_manage_products)
    staff_user3.user_permissions.add(permission_manage_orders)

    group = permission_group_manage_users
    group.user_set.add(staff_users[1], staff_user3)

    query = PERMISSION_GROUP_UPDATE_MUTATION

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "addUsers": [
                graphene.Node.to_global_id("User", user.id) for user in staff_users
            ],
            "removeUsers": [graphene.Node.to_global_id("User", staff_user3.id)],
        },
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert errors
    assert data["group"] is None
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "removeUsers"
    assert error["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_USER.name
    assert error["users"] == [graphene.Node.to_global_id("User", staff_user3.pk)]
    assert error["permissions"] is None

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not errors
    group = Group.objects.get()
    assert not errors
    permissions_codes = {
        permission["code"].lower() for permission in data["group"]["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
    assert variables["input"]["addPermissions"][0].lower() in permissions_codes
    group_users = group.user_set.all()
    assert staff_user3 not in group_users
    for staff in staff_users:
        assert staff in group_users


def test_permission_group_update_mutation_multiple_errors(
    permission_group_manage_users,
    staff_user,
    customer_user,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure update mutation failed with all validation errors when input data
    is incorrent:
        - adding permission which user hasn't (OUT_OF_SCOPE_PERMISSION)
        - adding customer user (ASSIGN_NON_STAFF_MEMBER)
    """

    staff_user.user_permissions.add(permission_manage_apps, permission_manage_users)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    user_ids = [
        graphene.Node.to_global_id("User", user.pk)
        for user in [staff_user, customer_user]
    ]
    permissions = [
        OrderPermissions.MANAGE_ORDERS.name,
        AppPermission.MANAGE_APPS.name,
    ]
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": permissions,
            "addUsers": user_ids[1],
            "removeUsers": user_ids[0],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 3
    expected_errors = [
        {
            "code": "OUT_OF_SCOPE_PERMISSION",
            "field": "addPermissions",
            "permissions": [OrderPermissions.MANAGE_ORDERS.codename],
            "users": None,
        },
        {
            "code": "ASSIGN_NON_STAFF_MEMBER",
            "field": "addUsers",
            "permissions": None,
            "users": user_ids[1],
        },
        {
            "code": "LEFT_NOT_MANAGEABLE_PERMISSION",
            "field": "removeUsers",
            "permissions": None,
            "users": user_ids[0],
        },
    ]
    for error in errors:
        error.pop("message")
        error in expected_errors
    assert data["group"] is None


def test_permission_group_update_mutation_remove_all_users_manageable_perms(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    staff_api_client,
):
    """Ensure that user can remove group users if there is other source of all group
    permissions."""
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff, order and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_staff, permission_manage_users)
    group2.permissions.add(
        permission_manage_staff, permission_manage_orders, permission_manage_users
    )

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {
            "removeUsers": [
                graphene.Node.to_global_id("User", user.id)
                for user in [staff_user1, staff_user2]
            ],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not errors
    assert data["group"]
    assert not data["group"]["users"]
    assert data["group"]["name"] == group1.name


def test_permission_group_update_mutation_remove_all_group_users_not_manageable_perms(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    staff_api_client,
    superuser_api_client,
):
    """Ensure that user cannot remove group users if there is no other source of some
    of group permission.
    Ensure superuser pass restrictions.
    """
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and orders")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_staff, permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {
            "removeUsers": [
                graphene.Node.to_global_id("User", user.id)
                for user in [staff_user1, staff_user2]
            ],
        },
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removeUsers"
    assert (
        errors[0]["code"]
        == PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    )
    assert errors[0]["permissions"] == [permission_manage_users.codename.upper()]

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not errors
    group1.refresh_from_db()
    group_users = group1.user_set.all()
    for staff in [staff_user1, staff_user2]:
        assert staff not in group_users


def test_permission_group_update_mutation_remove_group_users_add_with_manage_stuff(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    staff_api_client,
):
    """Ensure that user can remove all group users when adding somebody with
    manage staff permission.
    """
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_staff, permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {
            "removeUsers": [graphene.Node.to_global_id("User", staff_user1.id)],
            "addUsers": [graphene.Node.to_global_id("User", staff_user2.id)],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]
    group_data = data["group"]

    assert not errors
    assert group_data["name"] == group1.name
    assert len(group_data["users"]) == 1
    assert group_data["users"][0]["email"] == staff_user2.email


def test_group_update_mutation_remove_some_users_from_group_with_manage_stuff(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
):
    """Ensure that user can remove some of user group if group has manage
    staff permission.
    """
    staff_user, staff_user1, staff_user2 = staff_users
    group = permission_group_manage_users

    group.permissions.add(permission_manage_staff)

    group.user_set.add(staff_user1, staff_user2)

    staff_user.user_permissions.add(permission_manage_users)
    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"removeUsers": [graphene.Node.to_global_id("User", staff_user1.id)]},
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]
    group_data = data["group"]

    assert not errors
    assert group_data["name"] == group.name
    assert len(group_data["users"]) == 1
    assert group_data["users"][0]["email"] == staff_user2.email


def test_group_update_mutation_remove_some_users_from_group_user_with_manage_stuff(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_orders,
):
    """Ensure that user can remove some of user group from group without manage staff
    permission but some of the group member has manage staff permission from
    another source.
    """
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2)
    staff_user.user_permissions.add(permission_manage_users)
    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {"removeUsers": [graphene.Node.to_global_id("User", staff_user1.id)]},
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]
    group_data = data["group"]

    assert not errors
    assert group_data["name"] == group1.name
    assert len(group_data["users"]) == 1
    assert group_data["users"][0]["email"] == staff_user2.email


def test_permission_group_update_mutation_remove_user_with_manage_staff(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    staff_api_client,
):
    """Ensure user cannot remove users with manage staff permission from group if some
    permission will be no more manageable."""
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {
            "removeUsers": [
                graphene.Node.to_global_id("User", user.id) for user in [staff_user2]
            ],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removeUsers"
    assert (
        errors[0]["code"]
        == PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    )
    assert errors[0]["permissions"] == [permission_manage_users.codename.upper()]


def test_permission_group_update_mutation_remove_user_with_manage_staff_add_user(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    staff_api_client,
):
    """Ensure user can remove users with manage staff if user with manage staff
    will be added.
    """
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2, staff_user)

    staff_user.user_permissions.add(permission_manage_users)
    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group1.id),
        "input": {
            "removeUsers": [graphene.Node.to_global_id("User", staff_user2.id)],
            "addUsers": [graphene.Node.to_global_id("User", staff_user.id)],
        },
    }

    response = staff_api_client.post_graphql(
        query,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]
    group_data = data["group"]

    assert not errors
    assert group_data["name"] == group1.name
    assert len(group_data["users"]) == 2
    assert {user["email"] for user in group_data["users"]} == {
        staff_user1.email,
        staff_user.email,
    }


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
                code
                users
                permissions
                message
            }
        }
    }
    """


def test_group_delete_mutation(
    staff_users,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_products,
    staff_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(
        permission_manage_orders, permission_manage_products
    )
    groups = Group.objects.bulk_create(
        [Group(name="manage orders"), Group(name="manage orders and products")]
    )
    group1, group2 = groups
    group1.permissions.add(permission_manage_orders, permission_manage_staff)
    group2.permissions.add(
        permission_manage_orders, permission_manage_products, permission_manage_staff
    )

    staff_user2.groups.add(group1, group2)

    group1_name = group1.name
    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group1.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert errors == []
    assert permission_group_data["id"] == variables["id"]
    assert permission_group_data["name"] == group1_name
    assert permission_group_data["permissions"] == []


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_group_delete_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_users,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_products,
    staff_api_client,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(
        permission_manage_orders, permission_manage_products
    )
    groups = Group.objects.bulk_create(
        [Group(name="manage orders"), Group(name="manage orders and products")]
    )
    group1, group2 = groups
    group1.permissions.add(permission_manage_orders, permission_manage_staff)
    group2.permissions.add(
        permission_manage_orders, permission_manage_products, permission_manage_staff
    )

    staff_user2.groups.add(group1, group2)
    variables = {"id": graphene.Node.to_global_id("Group", group1.id)}

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_DELETE_MUTATION,
        variables,
        permissions=(permission_manage_staff,),
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]

    # then
    assert not data["errors"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Group", group1.id),
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.PERMISSION_GROUP_DELETED,
        [any_webhook],
        group1,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_group_delete_mutation_app_no_permission(
    staff_users,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_products,
    app_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(
        permission_manage_orders, permission_manage_products
    )
    groups = Group.objects.bulk_create(
        [Group(name="manage orders"), Group(name="manage orders and products")]
    )
    group1, group2 = groups
    group1.permissions.add(permission_manage_orders, permission_manage_staff)
    group2.permissions.add(
        permission_manage_orders, permission_manage_products, permission_manage_staff
    )

    staff_user2.groups.add(group1, group2)

    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group1.id)}
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )

    assert_no_permission(response)


def test_group_delete_mutation_out_of_scope_permission(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
):
    """Ensure staff user can't delete group which is out of user's permission scope.
    Ensure superuser pass restrictions.
    """
    group = permission_group_manage_users
    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert not permission_group_data
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert errors[0]["field"] is None

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]
    permission_group_data = data["group"]

    assert not errors
    assert not Group.objects.filter(pk=group.pk).exists()


def test_group_delete_mutation_left_not_manageable_permission(
    staff_users,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_products,
    staff_api_client,
    superuser_api_client,
):
    """Ensure staff user can't delete group when some permissions will be not
    manageable.
    Ensure superuser pass restrictions.
    """
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(
        permission_manage_orders, permission_manage_products
    )
    groups = Group.objects.bulk_create(
        [
            Group(name="manage orders and products"),
            Group(name="manage products"),
            Group(name="manage staff"),
            Group(name="manage orders"),
        ]
    )
    group1, group2, group3, group4 = groups

    # add permissions to groups
    group1.permissions.add(
        permission_manage_orders, permission_manage_products, permission_manage_staff
    )
    group2.permissions.add(permission_manage_products)
    group3.permissions.add(permission_manage_staff)
    group4.permissions.add(permission_manage_orders)

    # add users to groups
    staff_user2.groups.add(group1, group2, group3)

    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group1.id)}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert (
        errors[0]["code"]
        == PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    )
    assert errors[0]["permissions"] == [OrderPermissions.MANAGE_ORDERS.name]

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]

    assert not errors
    assert not Group.objects.filter(pk=group1.pk).exists()


def test_group_delete_mutation_delete_last_group(
    staff_users,
    permission_group_manage_users,
    staff_api_client,
    permission_manage_staff,
    permission_manage_users,
):
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(permission_manage_users)
    group = permission_group_manage_users
    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert (
        errors[0]["code"]
        == PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    )
    assert errors[0]["permissions"] == [AccountPermissions.MANAGE_USERS.name]


def test_group_delete_mutation_delete_last_group_with_manage_staff(
    staff_users,
    permission_group_manage_users,
    staff_api_client,
    permission_manage_staff,
    permission_manage_users,
):
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(permission_manage_users)
    groups = Group.objects.bulk_create(
        [Group(name="manage users and staff"), Group(name="manage users")]
    )
    group1, group2 = groups
    group1.permissions.add(permission_manage_staff, permission_manage_users)
    group2.permissions.add(permission_manage_users)

    staff_user2.groups.add(group1, group2)

    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group1.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert (
        errors[0]["code"]
        == PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    )
    assert set(errors[0]["permissions"]) == {
        AccountPermissions.MANAGE_STAFF.name,
        AccountPermissions.MANAGE_USERS.name,
    }


def test_group_delete_mutation_cannot_remove_requestor_last_group(
    staff_users,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_products,
    staff_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.user_permissions.add(
        permission_manage_orders, permission_manage_products
    )
    groups = Group.objects.bulk_create(
        [Group(name="manage orders"), Group(name="manage orders and products")]
    )
    group1, group2 = groups
    group1.permissions.add(permission_manage_orders, permission_manage_staff)
    group2.permissions.add(
        permission_manage_orders, permission_manage_products, permission_manage_staff
    )

    staff_user2.groups.add(group1, group2)
    staff_user.groups.add(group1)

    query = PERMISSION_GROUP_DELETE_MUTATION

    variables = {"id": graphene.Node.to_global_id("Group", group1.id)}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]

    assert errors[0]["field"] == "id"
    assert (
        errors[0]["code"] == PermissionGroupErrorCode.CANNOT_REMOVE_FROM_LAST_GROUP.name
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
                    userCanManage
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
    query = QUERY_PERMISSION_GROUP_WITH_FILTER

    Group.objects.bulk_create(
        [Group(name="Manage product."), Group(name="Remove product.")]
    )

    variables = {"filter": permission_group_filter}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroups"]["edges"]

    assert len(data) == count


def test_permission_groups_query_with_filter_by_ids(
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
):
    # given
    query = QUERY_PERMISSION_GROUP_WITH_FILTER
    variables = {
        "filter": {
            "ids": [
                graphene.Node.to_global_id("Group", permission_group_manage_users.pk)
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["permissionGroups"]["edges"]
    assert len(data) == 1


def test_permission_groups_no_permission_to_perform(
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
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
    query = QUERY_PERMISSION_GROUP_WITH_SORT

    Group.objects.bulk_create([Group(name="Add"), Group(name="Remove")])

    variables = {"sort_by": permission_group_sort}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroups"]["edges"]

    for order, group_name in enumerate(result):
        assert data[order]["node"]["name"] == group_name


QUERY_PERMISSION_GROUP = """
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


def test_permission_group_query(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    permission_manage_users,
    staff_api_client,
):
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
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
    assert data["userCanManage"] is True


def test_permission_group_query_user_cannot_manage(
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
    assert data["userCanManage"] is False


def test_permission_group_no_permission_to_perform(
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
):
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_query_permission_group_by_invalid_id(
    staff_api_client,
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_staff,
):
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_PERMISSION_GROUP, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["permissionGroup"] is None


def test_query_permission_group_with_invalid_object_type(
    staff_api_client,
    staff_user,
    permission_group_manage_users,
    permission_manage_staff,
    permission_manage_users,
):
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    variables = {
        "id": graphene.Node.to_global_id("Order", permission_group_manage_users.pk)
    }
    response = staff_api_client.post_graphql(QUERY_PERMISSION_GROUP, variables)
    content = get_graphql_content(response)
    assert content["data"]["permissionGroup"] is None
