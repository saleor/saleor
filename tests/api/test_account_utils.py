from saleor.core.permissions import AccountPermissions, OrderPermissions
from saleor.graphql.account.utils import (
    can_user_manage_group,
    get_out_of_scope_permissions,
)


def test_can_manage_group_user_without_permissions(
    staff_user, permission_group_manage_users
):
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert not result


def test_can_manage_group_user_with_different_permissions(
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_orders)
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert not result


def test_can_manage_group_true(
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert result


def test_can_manage_group_user_superuser(
    admin_user, permission_group_manage_users, permission_manage_orders
):
    result = can_user_manage_group(admin_user, permission_group_manage_users)
    assert result


def test_get_out_of_scope_permissions_user_has_all_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    staff_user.user_permissions.add(permission_manage_orders, permission_manage_users)
    result = get_out_of_scope_permissions(
        staff_user, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    )
    assert not result


def test_get_out_of_scope_permissions_user_does_not_have_all_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    staff_user.user_permissions.add(permission_manage_orders)
    result = get_out_of_scope_permissions(
        staff_user, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    )
    assert result == [AccountPermissions.MANAGE_USERS]


def test_get_out_of_scope_permissions_user_without_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    permissions = [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    result = get_out_of_scope_permissions(staff_user, permissions)
    assert result == permissions
