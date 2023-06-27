import pytest
from mock import Mock

from ..auth_filters import AuthorizationFilters
from ..enums import CheckoutPermissions
from ..utils import one_of_permissions_or_auth_filter_required


@pytest.mark.parametrize(
    "permissions, expected_result",
    [
        (None, True),
        ([], True),
        ([CheckoutPermissions.MANAGE_CHECKOUTS], True),
        ([CheckoutPermissions.MANAGE_TAXES], False),
        (
            [CheckoutPermissions.MANAGE_CHECKOUTS, CheckoutPermissions.MANAGE_TAXES],
            True,
        ),
        ([AuthorizationFilters.AUTHENTICATED_APP], True),
        ([AuthorizationFilters.AUTHENTICATED_USER], False),
        (
            [
                AuthorizationFilters.AUTHENTICATED_APP,
                AuthorizationFilters.AUTHENTICATED_USER,
            ],
            True,
        ),
        ([AuthorizationFilters.AUTHENTICATED_STAFF_USER], False),
        (
            [
                AuthorizationFilters.AUTHENTICATED_APP,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            True,
        ),
        (
            [
                AuthorizationFilters.AUTHENTICATED_USER,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            False,
        ),
        (
            [CheckoutPermissions.MANAGE_TAXES, AuthorizationFilters.AUTHENTICATED_APP],
            True,
        ),
        (
            [
                CheckoutPermissions.MANAGE_TAXES,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            False,
        ),
        (
            [CheckoutPermissions.MANAGE_TAXES, AuthorizationFilters.AUTHENTICATED_USER],
            False,
        ),
    ],
)
def test_permissions_for_app(
    permissions, expected_result, app, permission_manage_checkouts
):
    # given
    app.permissions.set([permission_manage_checkouts])
    context = Mock()
    context.app = app
    context.user = None

    # when
    result = one_of_permissions_or_auth_filter_required(context, permissions)

    # then
    assert result == expected_result


@pytest.mark.parametrize(
    "permissions, expected_result",
    [
        (None, True),
        ([], True),
        ([CheckoutPermissions.MANAGE_CHECKOUTS], True),
        ([CheckoutPermissions.MANAGE_TAXES], False),
        (
            [CheckoutPermissions.MANAGE_CHECKOUTS, CheckoutPermissions.MANAGE_TAXES],
            True,
        ),
        ([AuthorizationFilters.AUTHENTICATED_APP], False),
        ([AuthorizationFilters.AUTHENTICATED_USER], True),
        (
            [
                AuthorizationFilters.AUTHENTICATED_APP,
                AuthorizationFilters.AUTHENTICATED_USER,
            ],
            True,
        ),
        ([AuthorizationFilters.AUTHENTICATED_STAFF_USER], True),
        (
            [
                AuthorizationFilters.AUTHENTICATED_APP,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            True,
        ),
        (
            [
                AuthorizationFilters.AUTHENTICATED_USER,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            True,
        ),
        (
            [CheckoutPermissions.MANAGE_TAXES, AuthorizationFilters.AUTHENTICATED_APP],
            False,
        ),
        (
            [
                CheckoutPermissions.MANAGE_TAXES,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            True,
        ),
        (
            [CheckoutPermissions.MANAGE_TAXES, AuthorizationFilters.AUTHENTICATED_USER],
            True,
        ),
    ],
)
def test_permissions_for_staff_user(
    permissions, expected_result, staff_user, permission_manage_checkouts
):
    # given
    staff_user.user_permissions.set([permission_manage_checkouts])
    context = Mock()
    context.app = None
    context.user = staff_user

    # when
    result = one_of_permissions_or_auth_filter_required(context, permissions)

    # then
    assert result is expected_result


@pytest.mark.parametrize(
    "permissions, expected_result",
    [
        (None, True),
        ([], True),
        ([CheckoutPermissions.MANAGE_CHECKOUTS], False),
        ([CheckoutPermissions.MANAGE_TAXES], False),
        (
            [CheckoutPermissions.MANAGE_CHECKOUTS, CheckoutPermissions.MANAGE_TAXES],
            False,
        ),
        ([AuthorizationFilters.AUTHENTICATED_APP], False),
        ([AuthorizationFilters.AUTHENTICATED_USER], True),
        (
            [
                AuthorizationFilters.AUTHENTICATED_APP,
                AuthorizationFilters.AUTHENTICATED_USER,
            ],
            True,
        ),
        ([AuthorizationFilters.AUTHENTICATED_STAFF_USER], False),
        (
            [
                AuthorizationFilters.AUTHENTICATED_APP,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            False,
        ),
        (
            [
                AuthorizationFilters.AUTHENTICATED_USER,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            True,
        ),
        (
            [CheckoutPermissions.MANAGE_TAXES, AuthorizationFilters.AUTHENTICATED_APP],
            False,
        ),
        (
            [
                CheckoutPermissions.MANAGE_TAXES,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
            False,
        ),
        (
            [CheckoutPermissions.MANAGE_TAXES, AuthorizationFilters.AUTHENTICATED_USER],
            True,
        ),
    ],
)
def test_permissions_for_customer(permissions, expected_result, customer_user):
    # given
    context = Mock()
    context.app = None
    context.user = customer_user

    # when
    result = one_of_permissions_or_auth_filter_required(context, permissions)

    # then
    assert result is expected_result
