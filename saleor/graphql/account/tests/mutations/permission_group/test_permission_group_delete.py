import json
from unittest.mock import patch

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ......account.error_codes import PermissionGroupErrorCode
from ......account.models import Group
from ......core.utils.json_serializer import CustomJsonEncoder
from ......permission.enums import AccountPermissions, OrderPermissions
from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.payloads import generate_meta, generate_requestor
from .....tests.utils import assert_no_permission, get_graphql_content

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
        allow_replica=False,
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
    staff_api_client,
    permission_manage_staff,
    permission_group_manage_users,
):
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.groups.add(permission_group_manage_users)
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
    staff_user.groups.add(permission_group_manage_users)
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


def test_group_delete_mutation_no_channel_access(
    staff_users,
    permission_group_all_perms_channel_USD_only,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_products,
    staff_api_client,
):
    # given
    staff_user, staff_user1, staff_user2 = staff_users
    staff_user.groups.add(permission_group_all_perms_channel_USD_only)
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

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    errors = data["errors"]

    assert not data["group"]
    assert len(errors) == 1
    assert errors[0]["code"] == PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.name
