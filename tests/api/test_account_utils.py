from saleor.graphql.account.utils import can_user_manage_group


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
