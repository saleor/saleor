import json
from unittest.mock import patch

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ......account.error_codes import PermissionGroupErrorCode
from ......account.models import Group, User
from ......channel.models import Channel
from ......core.utils.json_serializer import CustomJsonEncoder
from ......permission.enums import AccountPermissions, AppPermission, OrderPermissions
from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.payloads import generate_meta, generate_requestor
from .....tests.utils import assert_no_permission, get_graphql_content

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
                restrictedAccessToChannels
                accessibleChannels {
                    slug
                }
            }
            errors{
                field
                code
                permissions
                users
                channels
                message
            }
        }
    }
    """


def test_permission_group_update_mutation(
    staff_users,
    staff_api_client,
    permission_group_manage_apps,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_staff,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_apps, permission_group_manage_users)
    query = PERMISSION_GROUP_UPDATE_MUTATION

    group1, group2 = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_users, permission_manage_staff)

    group1_user = staff_users[1]
    group1.user_set.add(group1_user)
    group2.user_set.add(staff_user)

    group1.restricted_access_to_channels = True
    group1.save(update_fields=["restricted_access_to_channels"])

    group1.channels.add(channel_USD)

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
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
            "removeChannels": [graphene.Node.to_global_id("Channel", channel_USD.pk)],
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
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
    assert permission_group_data["restrictedAccessToChannels"] is True
    assert len(permission_group_data["accessibleChannels"]) == 1
    assert permission_group_data["accessibleChannels"][0]["slug"] == channel_PLN.slug
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
    permission_manage_users,
    staff_api_client,
    permission_group_manage_apps,
    permission_group_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_apps, permission_group_manage_users)
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
        allow_replica=False,
    )


def test_permission_group_update_mutation_to_not_restricted_channels(
    permission_group_no_perms_all_channels,
    permission_group_all_perms_channel_USD_only,
    staff_api_client,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_api_client.user
    group = permission_group_all_perms_channel_USD_only
    staff_user.groups.add(
        permission_group_no_perms_all_channels,
        permission_group_all_perms_channel_USD_only,
    )

    assert group.channels.count() > 0

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "restrictedAccessToChannels": False,
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]
    assert data["errors"] == []
    assert permission_group_data["restrictedAccessToChannels"] is False
    assert len(permission_group_data["accessibleChannels"]) == Channel.objects.count()
    group.refresh_from_db()
    assert group.channels.count() == 0


def test_permission_group_update_mutation_to_not_restricted_channels_no_access(
    permission_group_all_perms_channel_USD_only,
    staff_api_client,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_api_client.user
    group = permission_group_all_perms_channel_USD_only
    group.user_set.add(staff_user)

    assert group.channels.count() > 0

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "restrictedAccessToChannels": False,
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    assert not data["group"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "restrictedAccessToChannels"
    assert (
        data["errors"][0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.name
    )


def test_permission_group_update_mutation_to_not_restricted_channels_superuser(
    permission_group_all_perms_channel_USD_only,
    superuser_api_client,
    channel_PLN,
    channel_USD,
):
    # given
    group = permission_group_all_perms_channel_USD_only

    assert group.channels.count() > 0

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "restrictedAccessToChannels": False,
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        },
    }

    # when
    response = superuser_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]
    assert data["errors"] == []
    assert permission_group_data["restrictedAccessToChannels"] is False
    assert len(permission_group_data["accessibleChannels"]) == Channel.objects.count()
    group.refresh_from_db()
    assert group.channels.count() == 0


def test_permission_group_update_mutation_not_restricted_channels(
    permission_group_all_perms_all_channels,
    staff_api_client,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_api_client.user
    group = permission_group_all_perms_all_channels
    group.user_set.add(staff_user)

    assert group.channels.count() == 0

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]
    assert data["errors"] == []
    assert permission_group_data["restrictedAccessToChannels"] is False
    assert len(permission_group_data["accessibleChannels"]) == Channel.objects.count()
    group.refresh_from_db()
    assert group.channels.count() == 0


def test_permission_group_update_mutation_no_channel_access(
    permission_group_all_perms_channel_USD_only,
    staff_api_client,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_api_client.user
    group = permission_group_all_perms_channel_USD_only
    group.user_set.add(staff_user)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"addChannels": [channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addChannels"
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.name
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] is None
    assert errors[0]["channels"] == [channel_id]


def test_permission_group_update_mutation_out_of_scope_channel(
    permission_group_all_perms_channel_USD_only,
    permission_group_no_perms_all_channels,
    staff_api_client,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_api_client.user
    permission_group_all_perms_channel_USD_only.user_set.add(staff_user)
    group = permission_group_no_perms_all_channels

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"name": "New name"},
    }

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.name
    assert errors[0]["permissions"] is None
    assert errors[0]["users"] is None
    assert errors[0]["channels"] is None


def test_permission_group_update_mutation_removing_perm_left_not_manageable_perms(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_apps,
    permission_group_manage_users,
):
    """Ensure user cannot remove permissions if it left not meanagable perms."""
    staff_api_client.user.groups.add(
        permission_group_manage_apps, permission_group_manage_users
    )
    group = permission_group_manage_users
    query = PERMISSION_GROUP_UPDATE_MUTATION

    group_user = group.user_set.first()
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": "New permission group",
            "addPermissions": [AppPermission.MANAGE_APPS.name],
            "removePermissions": [AccountPermissions.MANAGE_USERS.name],
            "addUsers": [graphene.Node.to_global_id("User", staff_users[-1].pk)],
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
    assert staff_users[-1].groups.count() == 0


def test_permission_group_update_mutation_superuser_can_remove_any_perms(
    permission_manage_staff,
    superuser_api_client,
    staff_user,
    permission_group_manage_apps,
    permission_group_manage_users,
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
    staff_user,
    permission_manage_staff,
    app_api_client,
    permission_group_manage_apps,
    permission_group_manage_users,
):
    staff_user.groups.add(permission_group_manage_apps, permission_group_manage_users)
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
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
):
    """Ensure mutation failed when user removing himself from user's last group."""
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.groups.add(permission_group_manage_users)
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
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_manage_orders,
    permission_manage_users,
):
    """Ensure user can remove himself from group if he is a member of another group."""
    staff_user, staff_user1, _ = staff_users
    staff_user.groups.add(permission_group_manage_users)
    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_users, permission_manage_staff)

    # ensure user is in group
    group1.user_set.add(staff_user)
    group2.user_set.add(staff_user, staff_user1)

    assert staff_user.groups.count() == 3

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
    assert staff_user.groups.count() == 2


def test_permission_group_update_mutation_remove_last_user_from_group(
    permission_group_manage_users,
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    """Ensure user can remove last user from the group."""
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.groups.add(permission_group_manage_users)
    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups
    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_users, permission_manage_staff)

    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)
    assert staff_user.groups.count() == 1

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
    assert staff_user.groups.count() == 1
    assert permission_group_data["users"] == []


def test_permission_group_update_mutation_only_name(
    permission_group_manage_users,
    permission_group_manage_staff,
    staff_user,
    staff_api_client,
    permission_manage_users,
):
    """Ensure mutation update group when only name are passed in input."""
    staff_user.groups.add(permission_group_manage_staff, permission_group_manage_users)
    group = permission_group_manage_users
    old_group_name = group.name
    query = PERMISSION_GROUP_UPDATE_MUTATION
    name = "New permission group"

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"name": name},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    permission_group_data = data["group"]

    group = Group.objects.get(name=name)
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
    permission_group_manage_staff,
    staff_api_client,
    permission_manage_users,
):
    """Ensure mutation update group when only name are passed in input."""
    staff_user.groups.add(permission_group_manage_staff, permission_group_manage_users)
    group = permission_group_manage_users
    old_group_name = group.name
    query = PERMISSION_GROUP_UPDATE_MUTATION
    name = "New permission group"

    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "name": name,
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

    group = Group.objects.get(name=name)
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
    permission_group_manage_staff,
    staff_user,
    staff_api_client,
):
    staff_user.groups.add(permission_group_manage_staff, permission_group_manage_users)
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
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
):
    """Ensure mutation update group when only permissions are passed in input."""
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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

    group.refresh_from_db()
    assert group.name == old_group_name
    assert permission_group_data["name"] == group.name
    permissions = {
        permission["name"] for permission in permission_group_data["permissions"]
    }
    assert set(group.permissions.all().values_list("name", flat=True)) == permissions
    assert data["errors"] == []


def test_permission_group_update_mutation_no_input_data(
    staff_user,
    permission_group_manage_users,
    permission_group_manage_staff,
    staff_api_client,
):
    """Ensure mutation doesn't change group when input is empty."""
    staff_user.groups.add(permission_group_manage_staff, permission_group_manage_users)
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
    permission_group_manage_apps,
):
    staff_user.groups.add(permission_group_manage_apps)
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
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    permission_group_manage_orders,
):
    staff_user.groups.add(
        permission_group_manage_users,
        permission_group_manage_apps,
        permission_group_manage_orders,
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
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    permission_group_manage_orders,
):
    staff_user = staff_users[0]
    staff_user.groups.add(
        permission_group_manage_users,
        permission_group_manage_apps,
        permission_group_manage_orders,
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
    staff_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    customer_user,
):
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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
    staff_user,
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    permission_manage_orders,
):
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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
    permission_manage_staff,
    staff_api_client,
    superuser_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    permission_manage_orders,
    permission_manage_products,
):
    staff_user = staff_users[0]
    staff_user3 = User.objects.create_user(
        email="staff3_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    staff_user.groups.add(permission_group_manage_apps, permission_group_manage_users)
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
    group.refresh_from_db()
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


def test_permission_group_update_mutation_duplicated_channels(
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    channel_PLN,
    channel_USD,
    channel_JPY,
):
    # given
    staff_user.groups.add(
        permission_group_manage_users,
        permission_group_manage_apps,
    )
    group = permission_group_manage_users

    query = PERMISSION_GROUP_UPDATE_MUTATION

    add_channels = [
        graphene.Node.to_global_id("Channel", channel)
        for channel in [channel_PLN, channel_USD, channel_JPY]
    ]
    remove_channels = [
        graphene.Node.to_global_id("Channel", channel)
        for channel in [channel_USD, channel_JPY]
    ]
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {
            "addChannels": add_channels,
            "removeChannels": remove_channels,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "channels"
    assert set(errors[0]["channels"]) == {
        graphene.Node.to_global_id("Channel", channel)
        for channel in [channel_USD, channel_JPY]
    }
    assert errors[0]["users"] is None
    assert errors[0]["permissions"] is None


def test_permission_group_update_mutation_multiple_errors(
    staff_user,
    customer_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    permission_manage_orders,
):
    staff_user.groups.add(permission_group_manage_apps, permission_group_manage_users)
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
            "channels": None,
            "code": "OUT_OF_SCOPE_PERMISSION",
            "field": "addPermissions",
            "permissions": [OrderPermissions.MANAGE_ORDERS.name],
            "users": None,
        },
        {
            "channels": None,
            "code": "ASSIGN_NON_STAFF_MEMBER",
            "field": "addUsers",
            "permissions": None,
            "users": [user_ids[1]],
        },
        {
            "channels": None,
            "code": "LEFT_NOT_MANAGEABLE_PERMISSION",
            "field": "removeUsers",
            "permissions": [AccountPermissions.MANAGE_USERS.name],
            "users": None,
        },
    ]
    for error in errors:
        error.pop("message")
        assert error in expected_errors
    assert data["group"] is None


def test_permission_group_update_mutation_remove_all_users_manageable_perms(
    staff_users,
    permission_group_manage_users,
    permission_group_manage_orders,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_users,
    staff_api_client,
):
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

    staff_user.groups.add(permission_group_manage_users, permission_group_manage_orders)
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
    permission_group_manage_users,
    permission_group_manage_orders,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
    staff_api_client,
    superuser_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and orders")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_staff, permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2)

    staff_user.groups.add(permission_group_manage_users, permission_group_manage_orders)
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
    permission_group_manage_users,
    permission_group_manage_orders,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_users,
    staff_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_staff, permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)

    staff_user.groups.add(permission_group_manage_users, permission_group_manage_orders)
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


def test_group_update_mutation_remove_some_users_from_group_with_manage_staff(
    staff_users,
    permission_group_manage_users,
    permission_group_manage_staff,
    permission_manage_staff,
    staff_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users
    group = permission_group_manage_users
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_staff)

    group.permissions.add(permission_manage_staff)
    group.user_set.add(staff_user1, staff_user2)

    assert group.user_set.count() == 3

    query = PERMISSION_GROUP_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Group", group.id),
        "input": {"removeUsers": [graphene.Node.to_global_id("User", staff_user1.id)]},
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    errors = data["errors"]
    group_data = data["group"]

    assert not errors
    assert group_data["name"] == group.name
    assert len(group_data["users"]) == 2
    assert staff_user1.email not in [user["email"] for user in group_data["users"]]


def test_group_update_mutation_remove_some_users_from_group_user_with_manage_stuff(
    staff_users,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_staff,
    staff_api_client,
    permission_manage_orders,
):
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2)
    staff_user.groups.add(permission_group_manage_users)
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
    permission_group_manage_users,
    permission_group_manage_orders,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    staff_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2)

    staff_user.groups.add(permission_group_manage_users, permission_group_manage_orders)
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
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    staff_api_client,
):
    staff_user, staff_user1, staff_user2 = staff_users

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2, staff_user)

    staff_user.groups.add(permission_group_manage_users)
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
