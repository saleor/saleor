from django.contrib.auth.models import Group

from ....account.models import User
from ....app.models import App
from ....core.permissions import (
    AccountPermissions,
    OrderPermissions,
    ProductPermissions,
)
from ..utils import (
    can_manage_app,
    can_user_manage_group,
    get_group_permission_codes,
    get_group_to_permissions_and_users_mapping,
    get_groups_which_user_can_manage,
    get_not_manageable_permissions_after_group_deleting,
    get_not_manageable_permissions_after_removing_perms_from_group,
    get_not_manageable_permissions_after_removing_users_from_group,
    get_not_manageable_permissions_when_deactivate_or_remove_users,
    get_out_of_scope_permissions,
    get_out_of_scope_users,
    get_user_permissions,
    get_users_and_look_for_permissions_in_groups_with_manage_staff,
    is_owner_or_has_one_of_perms,
    look_for_permission_in_users_with_manage_staff,
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
    missing_perms = get_out_of_scope_permissions(
        staff_user, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    )
    assert missing_perms == []


def test_get_out_of_scope_permissions_user_does_not_have_all_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    staff_user.user_permissions.add(permission_manage_orders)
    missing_perms = get_out_of_scope_permissions(
        staff_user, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    )
    assert missing_perms == [AccountPermissions.MANAGE_USERS]


def test_get_out_of_scope_permissions_user_without_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    permissions = [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    missing_perms = get_out_of_scope_permissions(staff_user, permissions)
    assert missing_perms == permissions


def test_get_out_of_scope_permissions_app_has_all_permissions(
    app, permission_manage_orders, permission_manage_users
):
    app.permissions.add(permission_manage_orders, permission_manage_users)
    missing_perms = get_out_of_scope_permissions(
        app,
        [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS],
    )
    assert missing_perms == []


def test_get_out_of_scope_permissions_app_does_not_have_all_permissions(
    app, permission_manage_orders, permission_manage_users
):
    app.permissions.add(permission_manage_orders)
    missing_perms = get_out_of_scope_permissions(
        app,
        [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS],
    )
    assert missing_perms == [AccountPermissions.MANAGE_USERS]


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


def test_get_groups_which_user_can_manage(
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
    permission_manage_products,
):
    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)

    manage_orders_group = Group.objects.create(name="manage orders")
    manage_orders_group.permissions.add(permission_manage_orders)

    manage_orders_products_and_orders = Group.objects.create(
        name="manage orders and products"
    )
    manage_orders_products_and_orders.permissions.add(
        permission_manage_orders, permission_manage_products
    )

    no_permissions_group = Group.objects.create(name="empty group")

    group_result = get_groups_which_user_can_manage(staff_user)

    assert set(group_result) == {
        no_permissions_group,
        permission_group_manage_users,
        manage_orders_group,
    }


def test_get_groups_which_user_can_manage_admin_user(
    admin_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
    permission_manage_products,
):
    manage_orders_group = Group.objects.create(name="manage orders")
    manage_orders_group.permissions.add(permission_manage_orders)

    manage_orders_products_and_orders = Group.objects.create(
        name="manage orders and products"
    )
    manage_orders_products_and_orders.permissions.add(
        permission_manage_orders, permission_manage_products
    )

    Group.objects.create(name="empty group")

    group_result = get_groups_which_user_can_manage(admin_user)

    assert set(group_result) == set(Group.objects.all())


def test_get_groups_which_user_can_manage_customer_user(
    customer_user,
    permission_group_manage_users,
):
    Group.objects.create(name="empty group")

    group_result = get_groups_which_user_can_manage(customer_user)

    assert set(group_result) == set()


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


def test_get_group_to_permissions_and_users_mapping(
    staff_users,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_users,
):
    staff_user1, staff_user2, staff_user3_not_active = staff_users
    staff_user3_not_active.is_active = False
    staff_user3_not_active.save()

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage orders and products"),
            Group(name="empty group"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_products, permission_manage_orders)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user3_not_active)
    group3.user_set.add(staff_user2, staff_user3_not_active)

    result = get_group_to_permissions_and_users_mapping()
    excepted_result = {
        group1.pk: {
            "permissions": {AccountPermissions.MANAGE_USERS.value},
            "users": {staff_user1.pk, staff_user2.pk},
        },
        group2.pk: {
            "permissions": {
                ProductPermissions.MANAGE_PRODUCTS.value,
                OrderPermissions.MANAGE_ORDERS.value,
            },
            "users": set(),
        },
        group3.pk: {"permissions": set(), "users": {staff_user2.pk}},
    }
    for pk, group_data in result.items():
        assert set(group_data.pop("permissions")) == excepted_result[pk]["permissions"]
        assert set(group_data.pop("users")) == excepted_result[pk]["users"]
        assert group_data == {}


def test_get_users_and_look_for_permissions_in_groups_with_manage_staff():
    groups_data = {
        1: {
            "permissions": {
                "account.manage_staff",
                "order.manage_orders",
                "product.manage_products",
                "checkout.manage_checkouts",
            },
            "users": {1, 2},
        },
        2: {
            "permissions": {
                "account.manage_staff",
                "order.manage_orders",
                "checkout.manage_checkouts",
            },
            "users": set(),
        },
        3: {
            "permissions": {"account.manage_staff", "product.manage_products"},
            "users": {3, 2},
        },
        4: {"permissions": {"checkout.manage_checkouts"}, "users": {2}},
    }
    group_pk = 1
    permissions_to_find = groups_data.pop(group_pk)["permissions"]

    users = get_users_and_look_for_permissions_in_groups_with_manage_staff(
        groups_data, permissions_to_find
    )

    assert users == {2, 3}
    assert permissions_to_find == {"checkout.manage_checkouts", "order.manage_orders"}


def test_look_for_permission_in_users_with_manage_staff():
    groups_data = {
        1: {
            "permissions": {
                "account.manage_staff",
                "order.manage_orders",
                "product.manage_products",
                "checkout.manage_checkouts",
            },
            "users": {1, 2},
        },
        2: {
            "permissions": {
                "account.manage_staff",
                "order.manage_orders",
                "checkout.manage_checkouts",
            },
            "users": set(),
        },
        3: {
            "permissions": {"account.manage_staff", "product.manage_products"},
            "users": {3, 2},
        },
        4: {
            "permissions": {"checkout.manage_checkouts", "discount.manage_discounts"},
            "users": {2},
        },
        5: {"permissions": set(), "users": {1, 2, 3}},
    }
    group_pk = 1
    permissions_to_find = groups_data.pop(group_pk)["permissions"]
    users_to_check = {2, 3}

    look_for_permission_in_users_with_manage_staff(
        groups_data, users_to_check, permissions_to_find
    )

    assert permissions_to_find == {"order.manage_orders"}


def test_get_not_manageable_permissions_after_group_deleting(
    staff_users,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_checkouts,
    permission_manage_staff,
    permission_manage_discounts,
):
    staff_user1, staff_user2, staff_user3 = staff_users

    groups = Group.objects.bulk_create(
        [
            Group(name="group to remove"),
            Group(name="group without users"),
            Group(name="group with users and manage_staff"),
            Group(name="group with user and without manage_staff"),
        ]
    )
    group1, group2, group3, group4 = groups

    group1.permissions.add(
        permission_manage_orders,
        permission_manage_products,
        permission_manage_checkouts,
        permission_manage_staff,
    )
    group2.permissions.add(permission_manage_orders, permission_manage_checkouts)
    group3.permissions.add(permission_manage_products, permission_manage_staff)
    group4.permissions.add(permission_manage_staff, permission_manage_discounts)

    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user1)
    group3.user_set.add(staff_user2, staff_user3)
    group4.user_set.add(staff_user1)

    non_managable_permissions = get_not_manageable_permissions_after_group_deleting(
        group1
    )
    assert non_managable_permissions == set()


def test_get_not_manageable_permissions_after_group_deleting_some_cannot_be_manage(
    staff_users,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_checkouts,
    permission_manage_staff,
    permission_manage_discounts,
):
    staff_user1, staff_user2, staff_user3 = staff_users

    groups = Group.objects.bulk_create(
        [
            Group(name="group to remove"),
            Group(name="group without users"),
            Group(name="group with users and manage_staff"),
            Group(name="group with user and without manage_staff"),
        ]
    )
    group1, group2, group3, group4 = groups

    group1.permissions.add(
        permission_manage_orders,
        permission_manage_products,
        permission_manage_checkouts,
        permission_manage_staff,
    )
    group2.permissions.add(
        permission_manage_staff, permission_manage_orders, permission_manage_checkouts
    )
    group3.permissions.add(permission_manage_products, permission_manage_staff)
    group4.permissions.add(permission_manage_checkouts, permission_manage_discounts)

    group1.user_set.add(staff_user1, staff_user2)
    group3.user_set.add(staff_user2, staff_user3)
    group4.user_set.add(staff_user2)

    non_managable_permissions = get_not_manageable_permissions_after_group_deleting(
        group1
    )
    assert non_managable_permissions == {"order.manage_orders"}


def test_get_not_manageable_permissions_removing_users_from_group(
    staff_users, permission_group_manage_users, permission_manage_staff
):
    """Ensure not returning permission when some of users stay in group and groups has
    manage staff permission.
    """
    group = permission_group_manage_users
    group.permissions.add(permission_manage_staff)
    group.user_set.add(*staff_users)

    missing_perms = get_not_manageable_permissions_after_removing_users_from_group(
        group, staff_users[1:]
    )

    assert not missing_perms


def test_get_not_manageable_perms_removing_users_from_group_user_from_group_can_manage(
    staff_users, permission_manage_users, permission_manage_staff
):
    """Ensure not returning permission for group without manage staff permission when
    some of remaining users from group has manage staff permission from other source.
    """
    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)

    staff_user1, staff_user2, _ = staff_users
    group1.user_set.add(*staff_users)
    group2.user_set.add(staff_user1)

    missing_perms = get_not_manageable_permissions_after_removing_users_from_group(
        group1, [staff_user2]
    )

    assert not missing_perms


def test_get_notmanageable_perms_removing_users_from_group_user_out_of_group_can_manage(
    staff_users, permission_manage_users, permission_manage_staff
):
    """Ensure not returning permission for group, when manageable of all permissions are
    ensure by other groups.
    """
    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage staff and users")]
    )
    group1, group2 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff, permission_manage_users)

    staff_user1, staff_user2, _ = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)

    missing_perms = get_not_manageable_permissions_after_removing_users_from_group(
        group1, [staff_user1]
    )

    assert not missing_perms


def test_get_not_manageable_perms_removing_users_from_group_some_cannot_be_manage(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
):
    """Ensure returning permission for group, when manageable of all permissions are not
    ensure by other groups.
    """
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
    group3.permissions.add(permission_manage_users, permission_manage_orders)

    staff_user1, staff_user2, _ = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)
    group3.user_set.add(staff_user1)

    missing_perms = get_not_manageable_permissions_after_removing_users_from_group(
        group1, [staff_user1]
    )

    assert missing_perms == {AccountPermissions.MANAGE_USERS.value}


def test_get_not_manageable_permissions_when_deactivate_or_remove_user_no_permissions(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
):
    """Ensure user can be deactivated or removed when manageable of all permissions are
    ensure by other users."""
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
    group3.permissions.add(permission_manage_users, permission_manage_orders)

    staff_user1, staff_user2, _ = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1)
    group3.user_set.add(staff_user2)

    missing_perms = get_not_manageable_permissions_when_deactivate_or_remove_users(
        [staff_user1]
    )

    assert not missing_perms


def test_get_not_manageable_permissions_when_deactivate_or_remove_users_some_perms(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
):
    """Ensure user cannot be deactivated or removed when manageable of all permissions
    are not ensure by other users."""
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

    staff_user1, staff_user2, staff_user3 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user3)
    group3.user_set.add(staff_user2)

    missing_perms = get_not_manageable_permissions_when_deactivate_or_remove_users(
        [staff_user1, staff_user2]
    )

    assert missing_perms == {
        AccountPermissions.MANAGE_USERS.value,
        OrderPermissions.MANAGE_ORDERS.value,
    }


def test_get_not_manageable_permissions_deactivate_or_remove_user_cant_manage_staff(
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
):
    """Ensure user can be deactivated when user doesn't have manage staff permission."""
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

    staff_user1, staff_user2, _ = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)
    group3.user_set.add(staff_user2)

    missing_perms = get_not_manageable_permissions_when_deactivate_or_remove_users(
        [staff_user1]
    )

    assert not missing_perms


def test_get_not_manageable_permissions_after_removing_perms_from_group_no_perms(
    staff_users,
    permission_manage_users,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_orders,
):
    """Ensure no permissions are returned when all perms will be manageable after removing
    permissions from group."""
    groups = Group.objects.bulk_create(
        [
            Group(name="manage users and products"),
            Group(name="manage staff"),
            Group(name="manage orders and users"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users, permission_manage_products)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders, permission_manage_users)

    staff_user1, staff_user2, staff_user3 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user3)
    group3.user_set.add(staff_user2)

    missing_perms = get_not_manageable_permissions_after_removing_perms_from_group(
        group1, [AccountPermissions.MANAGE_USERS.value]
    )

    assert not missing_perms


def test_get_not_manageable_permissions_after_removing_perms_from_group_some_cannot(
    staff_users,
    permission_manage_users,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_orders,
):
    """Ensure permissions are returned when not all perms will be manageable after
    removing permissions from group."""
    groups = Group.objects.bulk_create(
        [
            Group(name="manage users and products"),
            Group(name="manage staff"),
            Group(name="manage orders and products"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users, permission_manage_products)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders, permission_manage_products)

    staff_user1, staff_user2, staff_user3 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user3)
    group3.user_set.add(staff_user2)

    missing_perms = get_not_manageable_permissions_after_removing_perms_from_group(
        group1,
        [
            AccountPermissions.MANAGE_USERS.value,
            ProductPermissions.MANAGE_PRODUCTS.value,
        ],
    )

    assert missing_perms == {AccountPermissions.MANAGE_USERS.value}


def test_can_manage_app_no_permission(
    app,
    staff_user,
    permission_manage_products,
    permission_manage_apps,
):
    app.permissions.add(permission_manage_products)
    staff_user.user_permissions.add(permission_manage_apps)

    result = can_manage_app(staff_user, app)
    assert result is False


def test_can_manage_app_account(
    app,
    staff_user,
    permission_manage_products,
    permission_manage_apps,
):
    app.permissions.add(permission_manage_products)
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_products)

    result = can_manage_app(staff_user, app)
    assert result is True


def test_can_manage_app_for_app_no_permission(
    permission_manage_products,
    permission_manage_apps,
):
    apps = App.objects.bulk_create([App(name="sa1"), App(name="sa2")])
    apps[1].permissions.add(permission_manage_products)
    apps[0].permissions.add(permission_manage_apps)

    result = can_manage_app(apps[0], apps[1])
    assert result is False


def test_can_manage_app_for_app(
    permission_manage_products,
    permission_manage_apps,
):
    apps = App.objects.bulk_create([App(name="sa1"), App(name="sa2")])
    apps[1].permissions.add(permission_manage_products)
    apps[0].permissions.add(permission_manage_apps, permission_manage_products)

    result = can_manage_app(apps[0], apps[1])
    assert result is True


def test_requestor_has_access_no_access_by_customer(staff_user, customer_user):
    # when
    result = is_owner_or_has_one_of_perms(
        customer_user, staff_user, OrderPermissions.MANAGE_ORDERS
    )

    # then
    assert result is False


def test_requestor_has_access_access_by_customer(customer_user):
    # when
    result = is_owner_or_has_one_of_perms(
        customer_user, customer_user, OrderPermissions.MANAGE_ORDERS
    )

    # then
    assert result is True


def test_requestor_has_access_access_by_staff(
    customer_user, staff_user, permission_manage_orders
):
    # given
    staff_user.user_permissions.add(permission_manage_orders)
    staff_user.save()

    # when
    result = is_owner_or_has_one_of_perms(
        staff_user, customer_user, OrderPermissions.MANAGE_ORDERS
    )

    # then
    assert result is True


def test_requestor_has_access_no_access_by_staff(
    customer_user, staff_user, permission_manage_products
):
    # given
    staff_user.user_permissions.add(permission_manage_products)
    staff_user.save()

    # when
    result = is_owner_or_has_one_of_perms(
        staff_user, customer_user, OrderPermissions.MANAGE_ORDERS
    )

    # then
    assert result is False
