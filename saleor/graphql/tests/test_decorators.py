import pytest
from django.contrib.auth.models import Permission

from ...core.permissions import (
    AppPermission,
    CheckoutPermissions,
    OrderPermissions,
    get_permissions_from_names,
)
from ..decorators import _permission_required


@pytest.mark.parametrize(
    "permissions_required, effective_permissions, user_permissions, access_granted",
    [
        ([AppPermission.MANAGE_APPS], ["MANAGE_APPS"], ["manage_apps"], True),
        (
            [AppPermission.MANAGE_APPS],
            ["MANAGE_APPS", "MANAGE_ORDERS", "MANAGE_CHECKOUTS"],
            ["manage_apps", "manage_orders", "manage_checkouts"],
            True,
        ),
        (
            [OrderPermissions.MANAGE_ORDERS, CheckoutPermissions.MANAGE_CHECKOUTS],
            ["MANAGE_ORDERS"],
            ["manage_orders"],
            False,
        ),
        ([OrderPermissions.MANAGE_ORDERS], ["MANAGE_APPS"], ["manage_apps"], False),
        ([CheckoutPermissions.MANAGE_CHECKOUTS], [], ["manage_checkouts"], False),
        ([CheckoutPermissions.MANAGE_CHECKOUTS], ["MANAGE_APPS"], [], False),
    ],
)
def test_permission_required_with_limited_permissions(
    permissions_required,
    effective_permissions,
    user_permissions,
    access_granted,
    staff_user,
    rf,
):
    staff_user.user_permissions.set(
        Permission.objects.filter(codename__in=user_permissions)
    )
    staff_user.effective_permissions = get_permissions_from_names(effective_permissions)
    request = rf.request()
    request.user = staff_user
    has_perms = _permission_required(permissions_required, request)
    assert has_perms == access_granted


@pytest.mark.parametrize(
    "permissions_required, user_permissions, access_granted",
    [
        ([AppPermission.MANAGE_APPS], ["manage_apps"], True),
        (
            [AppPermission.MANAGE_APPS],
            ["manage_apps", "manage_orders", "manage_checkouts"],
            True,
        ),
        (
            [OrderPermissions.MANAGE_ORDERS, CheckoutPermissions.MANAGE_CHECKOUTS],
            ["manage_orders"],
            False,
        ),
        ([OrderPermissions.MANAGE_ORDERS], ["manage_apps"], False),
        ([CheckoutPermissions.MANAGE_CHECKOUTS], [], False),
    ],
)
def test_permission_required(
    permissions_required,
    user_permissions,
    access_granted,
    staff_user,
    rf,
):
    staff_user.user_permissions.set(
        Permission.objects.filter(codename__in=user_permissions)
    )
    request = rf.request()
    request.user = staff_user
    has_perms = _permission_required(permissions_required, request)
    assert has_perms == access_granted
