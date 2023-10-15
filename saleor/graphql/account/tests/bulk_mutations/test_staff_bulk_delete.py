from unittest.mock import patch

import graphene

from .....account.error_codes import AccountErrorCode
from .....account.models import Group, User
from .....permission.enums import AccountPermissions, OrderPermissions
from ....tests.utils import assert_no_permission, get_graphql_content

STAFF_BULK_DELETE_MUTATION = """
    mutation staffBulkDelete($ids: [ID!]!) {
        staffBulkDelete(ids: $ids) {
            count
            errors{
                code
                field
                permissions
                users
            }
        }
    }
"""


def test_delete_staff_members(
    staff_api_client, user_list, permission_manage_staff, superuser
):
    *users, staff_1, staff_2 = user_list
    users.append(superuser)

    query = STAFF_BULK_DELETE_MUTATION

    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id) for user in [staff_1, staff_2]
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    assert data["count"] == 2
    assert not data["errors"]
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_1, staff_2]]
    ).exists()
    assert User.objects.filter(id__in=[user.id for user in users]).count() == len(users)


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_staff_members_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    user_list,
    permission_manage_staff,
    superuser,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    *users, staff_1, staff_2 = user_list
    users.append(superuser)

    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id) for user in [staff_1, staff_2]
        ]
    }
    response = staff_api_client.post_graphql(
        STAFF_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    assert data["count"] == 2
    assert not data["errors"]
    assert mocked_webhook_trigger.call_count == 2


def test_delete_staff_members_app_no_permission(
    app_api_client, user_list, permission_manage_staff, superuser
):
    *users, staff_1, staff_2 = user_list
    users.append(superuser)

    query = STAFF_BULK_DELETE_MUTATION

    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id) for user in [staff_1, staff_2]
        ]
    }
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    assert_no_permission(response)


def test_delete_staff_members_left_not_manageable_permissions(
    staff_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
):
    """Ensure user can't delete users when some permissions will be not manageable."""
    query = STAFF_BULK_DELETE_MUTATION

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage orders"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders)

    staff_user, staff_user1, staff_user2 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user)
    group3.user_set.add(staff_user1)

    staff_user.user_permissions.add(
        permission_manage_users, permission_manage_orders, permission_manage_staff
    )
    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id)
            for user in [staff_user1, staff_user2]
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    errors = data["errors"]

    assert len(errors) == 1
    assert data["count"] == 0
    assert errors[0]["field"] == "ids"
    assert errors[0]["code"] == AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    assert set(errors[0]["permissions"]) == {
        AccountPermissions.MANAGE_USERS.name,
        OrderPermissions.MANAGE_ORDERS.name,
    }
    assert User.objects.filter(
        id__in=[user.id for user in [staff_user1, staff_user2]]
    ).exists()


def test_delete_staff_members_superuser_can_delete_when_delete_left_notmanageable_perms(
    superuser_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
):
    """Ensure that superuser can delete users even when not all permissions which be
    manageable by other users.
    """
    query = STAFF_BULK_DELETE_MUTATION

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage orders"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders)

    staff_user, staff_user1, staff_user2 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user)
    group3.user_set.add(staff_user1)

    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id)
            for user in [staff_user1, staff_user2]
        ]
    }
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    errors = data["errors"]

    assert not errors
    assert data["count"] == 2
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_user1, staff_user2]]
    ).exists()


def test_delete_staff_members_all_permissions_manageable(
    staff_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
):
    """Ensure user can delete users when all permissions will be manageable."""
    query = STAFF_BULK_DELETE_MUTATION

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage users and orders"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders, permission_manage_users)

    staff_user, staff_user1, staff_user2 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user)
    group3.user_set.add(staff_user1, staff_user)

    staff_user.user_permissions.add(
        permission_manage_users, permission_manage_orders, permission_manage_staff
    )
    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id)
            for user in [staff_user1, staff_user2]
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    errors = data["errors"]

    assert not errors
    assert data["count"] == 2
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_user1, staff_user2]]
    ).exists()


def test_delete_staff_members_out_of_scope_users(
    staff_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
):
    """Ensure user can't delete users when some permissions will be not manageable."""
    query = STAFF_BULK_DELETE_MUTATION

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage orders and users"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders, permission_manage_users)

    staff_user, staff_user1, staff_user2 = staff_users
    staff_user3 = User.objects.create(
        email="staff3_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user3)
    group3.user_set.add(staff_user1, staff_user3)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_staff)
    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id)
            for user in [staff_user1, staff_user2]
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    errors = data["errors"]

    assert len(errors) == 1
    assert data["count"] == 0
    assert errors[0]["field"] == "ids"
    assert errors[0]["code"] == AccountErrorCode.OUT_OF_SCOPE_USER.name
    assert errors[0]["permissions"] is None
    assert set(errors[0]["users"]) == {
        graphene.Node.to_global_id("User", staff_user1.id)
    }
    assert User.objects.filter(
        id__in=[user.id for user in [staff_user1, staff_user2]]
    ).exists()


def test_delete_staff_members_superuser_can_delete__out_of_scope_users(
    superuser_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
):
    """Ensure superuser can delete users when
    some users has wider scope of permissions."""
    query = STAFF_BULK_DELETE_MUTATION

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage orders and users"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders, permission_manage_users)

    staff_user, staff_user1, staff_user2 = staff_users
    staff_user3 = User.objects.create(
        email="staff3_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user3)
    group3.user_set.add(staff_user1, staff_user3)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_staff)
    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id)
            for user in [staff_user1, staff_user2]
        ]
    }
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    errors = data["errors"]

    assert not errors
    assert data["count"] == 2
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_user1, staff_user2]]
    ).exists()
