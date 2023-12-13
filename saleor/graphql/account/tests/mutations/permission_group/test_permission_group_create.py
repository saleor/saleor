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
                message
                channels
            }
        }
    }
    """


def test_permission_group_create_mutation(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION
    name = "New permission group"

    variables = {
        "input": {
            "name": name,
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

    group = Group.objects.get(name=name)
    assert permission_group_data["name"] == group.name == variables["input"]["name"]
    assert permission_group_data["restrictedAccessToChannels"] is False
    assert len(permission_group_data["accessibleChannels"]) == Channel.objects.count()
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
    permission_group_manage_users,
    permission_group_manage_apps,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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
        allow_replica=False,
    )


def test_permission_group_create_app_no_permission(
    staff_users,
    permission_manage_staff,
    app_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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


def test_permission_group_create_no_channel_access(
    staff_users,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_users[0]
    permission_group_all_perms_channel_USD_only.user_set.add(staff_user)
    query = PERMISSION_GROUP_CREATE_MUTATION
    channel_PLN_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    channel_USD_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {
        "input": {
            "name": "New permission group",
            "restrictedAccessToChannels": True,
            "addPermissions": [
                AccountPermissions.MANAGE_USERS.name,
                AppPermission.MANAGE_APPS.name,
            ],
            "addUsers": [
                graphene.Node.to_global_id("User", user.id) for user in staff_users
            ],
            "addChannels": [channel_PLN_id, channel_USD_id],
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "addChannels"
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.name
    assert errors[0]["channels"] == [channel_PLN_id]


def test_permission_group_create_mutation_only_required_fields(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION
    name = "New permission group"

    variables = {"input": {"name": name}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]

    group = Group.objects.get(name=name)
    assert permission_group_data["name"] == group.name == variables["input"]["name"]
    assert permission_group_data["permissions"] == []
    assert not group.permissions.all()
    assert permission_group_data["users"] == []
    assert not group.user_set.all()


def test_permission_group_create_mutation_only_required_fields_not_none(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION
    name = "New permission group"

    variables = {
        "input": {
            "name": name,
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

    group = Group.objects.get(name=name)
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
    permission_group_manage_orders,
    permission_group_all_perms_all_channels,
):
    staff_user.groups.add(permission_group_manage_orders)
    query = PERMISSION_GROUP_CREATE_MUTATION
    name = "New permission group"

    variables = {
        "input": {
            "name": name,
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
    group = Group.objects.get(name=name)
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
    permission_group_manage_apps,
):
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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
    permission_group_manage_users,
    permission_group_manage_apps,
    permission_group_all_perms_all_channels,
):
    second_customer = User.objects.create(
        email="second_customer@test.com", password="test"
    )

    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
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
    permission_group_manage_users,
):
    staff_user.groups.add(permission_group_manage_users)
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
    permission_group_manage_apps,
):
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_apps)
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


def test_permission_group_create_mutation_restricted_access_to_channels(
    staff_users,
    permission_manage_staff,
    staff_api_client,
    permission_group_manage_users,
    permission_group_manage_apps,
    channel_PLN,
    channel_USD,
):
    # given
    staff_user = staff_users[0]
    staff_user.groups.add(permission_group_manage_users, permission_group_manage_apps)
    query = PERMISSION_GROUP_CREATE_MUTATION

    variables = {
        "input": {
            "name": "New permission group",
            "restrictedAccessToChannels": True,
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.id)],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]
    assert permission_group_data["name"] == variables["input"]["name"]
    assert permission_group_data["restrictedAccessToChannels"] is True
    assert len(permission_group_data["accessibleChannels"]) == 1
    assert permission_group_data["accessibleChannels"][0]["slug"] == channel_PLN.slug
    assert data["errors"] == []


def test_permission_group_create_mutation_not_restricted_channels(
    permission_manage_staff,
    staff_api_client,
    permission_group_no_perms_all_channels,
    channel_PLN,
    channel_USD,
):
    # given
    permission_group_no_perms_all_channels.user_set.add(staff_api_client.user)
    query = PERMISSION_GROUP_CREATE_MUTATION
    name = "New permission group"

    variables = {
        "input": {
            "name": name,
            "restrictedAccessToChannels": False,
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_staff,)
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["permissionGroupCreate"]
    permission_group_data = data["group"]
    assert data["errors"] == []
    assert permission_group_data["restrictedAccessToChannels"] is False
    assert len(permission_group_data["accessibleChannels"]) == Channel.objects.count()
    group = Group.objects.get(name=name)
    assert group.channels.count() == 0


def test_permission_group_create_mutation_not_restricted_channels_no_access(
    permission_manage_staff,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
    channel_USD,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    query = PERMISSION_GROUP_CREATE_MUTATION
    name = "New permission group"

    variables = {
        "input": {
            "name": name,
            "restrictedAccessToChannels": False,
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "restrictedAccessToChannels"
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.name
