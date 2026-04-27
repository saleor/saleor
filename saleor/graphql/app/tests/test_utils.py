import pytest
from django.core.exceptions import ValidationError

from ....app.error_codes import AppErrorCode
from ....permission.enums import (
    AccountPermissions,
    AppPermission,
    OrderPermissions,
    ProductPermissions,
)
from ..utils import ensure_app_permissions_allowed


def test_ensure_app_permissions_allowed_passes_when_no_manage_apps():
    permissions = [
        ProductPermissions.MANAGE_PRODUCTS.value,
        OrderPermissions.MANAGE_ORDERS.value,
    ]

    # when / then - does not raise
    ensure_app_permissions_allowed(permissions)


def test_ensure_app_permissions_allowed_passes_with_empty_list():
    # when / then - does not raise
    ensure_app_permissions_allowed([])


def test_ensure_app_permissions_allowed_rejects_manage_apps():
    permissions = [AppPermission.MANAGE_APPS.value]

    # when
    with pytest.raises(ValidationError) as exc_info:
        ensure_app_permissions_allowed(permissions)

    # then
    error = exc_info.value.error_dict["permissions"][0]
    assert error.code == AppErrorCode.OUT_OF_SCOPE_PERMISSION.value
    assert error.params == {"permissions": [AppPermission.MANAGE_APPS.value]}


def test_ensure_app_permissions_allowed_rejects_manage_apps_alongside_others():
    # given - MANAGE_APPS mixed with allowed permissions still rejects the whole input
    permissions = [
        ProductPermissions.MANAGE_PRODUCTS.value,
        AppPermission.MANAGE_APPS.value,
        AccountPermissions.MANAGE_USERS.value,
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        ensure_app_permissions_allowed(permissions)

    # then
    error = exc_info.value.error_dict["permissions"][0]
    assert error.code == AppErrorCode.OUT_OF_SCOPE_PERMISSION.value
    assert error.params == {"permissions": [AppPermission.MANAGE_APPS.value]}


def test_ensure_app_permissions_allowed_does_not_match_enum_name():
    # given - the enum NAME ("MANAGE_APPS") must not be confused with the dotted
    # codename ("app.manage_apps"). PermissionEnum input is deserialized as the
    # value, so an input list of just the name should not trigger the guard.
    permissions = ["MANAGE_APPS"]

    # when / then - does not raise; the helper compares against the dotted codename
    ensure_app_permissions_allowed(permissions)
