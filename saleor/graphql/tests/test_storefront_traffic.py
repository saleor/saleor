from types import SimpleNamespace

import pytest
from jwt import InvalidTokenError

from saleor.core.auth import SALEOR_AUTH_HEADER
from saleor.graphql.storefront_traffic import (
    clear_allow_storefront_traffic_cache,
    is_storefront_traffic_blocked,
)


def _make_request(app=None, user=None, authenticated=False):
    """Build a fake request. ``authenticated`` adds an auth token to the META.

    An anonymous request (no token) is short-circuited by the guard before
    ``request.user`` is resolved, so user-authenticated cases must carry a token.
    """
    meta = {SALEOR_AUTH_HEADER: "token"} if authenticated else {}
    return SimpleNamespace(app=app, user=user, META=meta)


def _set_allow_storefront_traffic(site_settings, allowed):
    site_settings.allow_storefront_traffic = allowed
    site_settings.save(update_fields=["allow_storefront_traffic"])
    clear_allow_storefront_traffic_cache()


@pytest.fixture(autouse=True)
def _clear_storefront_traffic_cache():
    clear_allow_storefront_traffic_cache()
    yield
    clear_allow_storefront_traffic_cache()


def test_blocks_anonymous_request_when_disabled(site_settings):
    # given
    _set_allow_storefront_traffic(site_settings, False)
    request = _make_request(app=None, user=None)

    # when / then
    assert is_storefront_traffic_blocked(request) is True


def test_allows_anonymous_request_when_enabled(site_settings):
    # given
    _set_allow_storefront_traffic(site_settings, True)
    request = _make_request(app=None, user=None)

    # when / then
    assert is_storefront_traffic_blocked(request) is False


def test_allows_app_request_when_disabled(site_settings, app):
    # given: an app is always allowed, regardless of the flag
    _set_allow_storefront_traffic(site_settings, False)
    request = _make_request(app=app, user=None)

    # when / then
    assert is_storefront_traffic_blocked(request) is False


@pytest.mark.parametrize(
    ("_case", "user_fixture", "allow_storefront_traffic", "expected_blocked"),
    [
        ("customer_disabled", "customer_user", False, True),
        ("customer_enabled", "customer_user", True, False),
        ("staff_disabled", "staff_user", False, False),
        ("staff_enabled", "staff_user", True, False),
    ],
)
def test_user_traffic(
    _case,
    user_fixture,
    allow_storefront_traffic,
    expected_blocked,
    request,
    site_settings,
):
    # given: a user-authenticated request — customers follow the flag, staff always allowed
    _set_allow_storefront_traffic(site_settings, allow_storefront_traffic)
    user = request.getfixturevalue(user_fixture)
    req = _make_request(app=None, user=user, authenticated=True)

    # when / then
    assert is_storefront_traffic_blocked(req) is expected_blocked


@pytest.mark.parametrize(
    ("_case", "allow_storefront_traffic", "expected_blocked"),
    [
        ("enabled", True, False),
        ("disabled", False, True),
    ],
)
def test_invalid_token_user_resolution(
    _case, allow_storefront_traffic, expected_blocked, site_settings
):
    # given: evaluating request.user raises for an invalid/stale token
    _set_allow_storefront_traffic(site_settings, allow_storefront_traffic)

    class Request:
        app = None
        META = {SALEOR_AUTH_HEADER: "token"}

        @property
        def user(self):
            raise InvalidTokenError("Invalid token.")

    # when / then
    assert is_storefront_traffic_blocked(Request()) is expected_blocked


def test_unexpected_user_object_is_not_privileged(site_settings):
    # given
    _set_allow_storefront_traffic(site_settings, False)
    request = _make_request(app=None, user=object(), authenticated=True)

    # when / then
    with pytest.warns(UserWarning, match="An invalid user object was found"):
        assert is_storefront_traffic_blocked(request) is True
