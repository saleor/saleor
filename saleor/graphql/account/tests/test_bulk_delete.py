from unittest.mock import patch

import graphene
from django.contrib.auth.models import Group

from ....account.error_codes import AccountErrorCode
from ....account.models import User
from ....core.permissions import AccountPermissions, OrderPermissions
from ...tests.utils import assert_no_permission, get_graphql_content


@patch(
    "saleor.graphql.account.utils.account_events.staff_user_deleted_a_customer_event"
)
def test_delete_customers(
    mocked_deletion_event,
    staff_api_client,
    staff_user,
    user_list,
    permission_manage_users,
):
    user_1, user_2, *users = user_list

    query = """
    mutation customerBulkDelete($ids: [ID]!) {
        customerBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    assert content["data"]["customerBulkDelete"]["count"] == 2

    deleted_customers = [user_1, user_2]
    saved_customers = users

    # Ensure given customers were properly deleted and others properly saved
    # and any related event was properly triggered

    # Ensure the customers were properly deleted and others were preserved
    assert not User.objects.filter(
        id__in=[user.id for user in deleted_customers]
    ).exists()
    assert User.objects.filter(
        id__in=[user.id for user in saved_customers]
    ).count() == len(saved_customers)

    mocked_deletion_event.assert_called_once_with(
        staff_user=staff_user, deleted_count=len(deleted_customers)
    )


STAFF_BULK_DELETE_MUTATION = """
    mutation staffBulkDelete($ids: [ID]!) {
        staffBulkDelete(ids: $ids) {
            count
            staffErrors{
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
    assert not data["staffErrors"]
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_1, staff_2]]
    ).exists()
    assert User.objects.filter(id__in=[user.id for user in users]).count() == len(users)


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
    errors = data["staffErrors"]

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
    errors = data["staffErrors"]

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
    errors = data["staffErrors"]

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
    errors = data["staffErrors"]

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
    errors = data["staffErrors"]

    assert not errors
    assert data["count"] == 2
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_user1, staff_user2]]
    ).exists()
