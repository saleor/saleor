from saleor.account.models import User
from saleor.core.permissions import AccountPermissions, OrderPermissions
from saleor.graphql.account.utils import (
    can_user_manage_group,
    get_group_permission_codes,
    get_out_of_scope_permissions,
    get_out_of_scope_users,
    get_user_permissions,
)


def test_can_manage_group_user_without_permissions(
    staff_user, permission_group_manage_users
):
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert result is False


def test_can_manage_group_user_with_different_permissions(
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_orders)
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert result is False


def test_can_manage_group(
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert result is True


def test_can_manage_group_user_superuser(
    admin_user, permission_group_manage_users, permission_manage_orders
):
    result = can_user_manage_group(admin_user, permission_group_manage_users)
    assert result is True


def test_get_out_of_scope_permissions_user_has_all_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    staff_user.user_permissions.add(permission_manage_orders, permission_manage_users)
    result = get_out_of_scope_permissions(
        staff_user, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    )
    assert result == []


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


def test_get_group_permission_codes(
    permission_group_manage_users, permission_manage_orders
):
    group = permission_group_manage_users
    permission_codes = get_group_permission_codes(group)

    expected_result = {
        f"{perm.content_type.app_label}.{perm.codename}"
        for perm in group.permissions.all()
    }
    assert len(permission_codes) == group.permissions.count()
    assert set(permission_codes) == expected_result


def test_get_group_permission_codes_group_without_permissions(
    permission_group_manage_users, permission_manage_orders
):
    group = permission_group_manage_users
    group.permissions.clear()
    permission_codes = get_group_permission_codes(group)

    assert len(permission_codes) == group.permissions.count()
    assert set(permission_codes) == set()


def test_get_user_permissions(permission_group_manage_users, permission_manage_orders):
    staff_user = permission_group_manage_users.user_set.first()
    group_permissions = permission_group_manage_users.permissions.all()
    staff_user.user_permissions.add(permission_manage_orders)

    permissions = get_user_permissions(staff_user)

    expected_permissions = group_permissions | staff_user.user_permissions.all()
    assert set(permissions.values_list("codename", flat=True)) == set(
        expected_permissions.values_list("codename", flat=True)
    )


def test_get_user_permissions_only_group_permissions(permission_group_manage_users):
    staff_user = permission_group_manage_users.user_set.first()
    group_permissions = permission_group_manage_users.permissions.all()

    permissions = get_user_permissions(staff_user)

    assert set(permissions.values_list("codename", flat=True)) == set(
        group_permissions.values_list("codename", flat=True)
    )


def test_get_user_permissions_only_permissions(staff_user, permission_manage_orders):
    staff_user.user_permissions.add(permission_manage_orders)

    permissions = get_user_permissions(staff_user)

    expected_permissions = staff_user.user_permissions.all()
    assert set(permissions.values_list("codename", flat=True)) == set(
        expected_permissions.values_list("codename", flat=True)
    )


def test_get_user_permissions_no_permissions(staff_user):
    permissions = get_user_permissions(staff_user)

    assert not permissions


def test_get_out_of_scope_users_user_has_rights_to_manage_all_users(
    staff_users,
    permission_group_manage_users,
    permission_manage_orders,
    permission_manage_products,
):
    staff_user1 = staff_users[0]
    staff_user2 = staff_users[1]
    staff_user3 = User.objects.create_user(
        email="staff3_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    permission_group_manage_users.user_set.add(staff_user1, staff_user2)
    staff_user1.user_permissions.add(
        permission_manage_products, permission_manage_orders
    )

    staff_user3.user_permissions.add(permission_manage_orders)

    users = User.objects.filter(pk__in=[staff_user1.pk, staff_user2.pk, staff_user3.pk])
    result_users = get_out_of_scope_users(staff_user1, users)

    assert result_users == []


def test_get_out_of_scope_users_for_admin_user(
    admin_user,
    staff_users,
    permission_group_manage_users,
    permission_manage_orders,
    permission_manage_products,
):
    staff_user1 = staff_users[0]
    staff_user2 = staff_users[1]

    permission_group_manage_users.user_set.add(staff_user1, staff_user2)
    staff_user1.user_permissions.add(
        permission_manage_products, permission_manage_orders
    )

    staff_user2.user_permissions.add(permission_manage_orders)

    users = User.objects.filter(pk__in=[staff_user1.pk, staff_user2.pk])
    result_users = get_out_of_scope_users(staff_user1, users)

    assert result_users == []


def test_get_out_of_scope_users_return_some_users(
    admin_user,
    staff_users,
    permission_group_manage_users,
    permission_manage_orders,
    permission_manage_products,
):
    staff_user1 = staff_users[0]
    staff_user2 = staff_users[1]
    staff_user3 = User.objects.create_user(
        email="staff3_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    permission_group_manage_users.user_set.add(staff_user1, staff_user2)

    staff_user3.user_permissions.add(
        permission_manage_products, permission_manage_orders
    )
    staff_user2.user_permissions.add(permission_manage_orders)

    users = User.objects.filter(pk__in=[staff_user1.pk, staff_user2.pk, staff_user3.pk])
    result_users = get_out_of_scope_users(staff_user1, users)

    assert result_users == [staff_user2, staff_user3]
