from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from jwt import InvalidTokenError

from saleor.core.auth import SALEOR_AUTH_HEADER
from saleor.graphql.storefront_traffic import (
    _get_allow_storefront_traffic_cache_key,
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
    ("_case", "allow_storefront_traffic", "expected_blocked", "expected_user_reads"),
    [
        # The flag alone settles the allowed case, so the user is never resolved.
        ("enabled", True, False, 0),
        ("disabled", False, True, 1),
    ],
)
def test_invalid_token_user_resolution(
    _case,
    allow_storefront_traffic,
    expected_blocked,
    expected_user_reads,
    site_settings,
):
    # given: evaluating request.user raises for an invalid/stale token
    _set_allow_storefront_traffic(site_settings, allow_storefront_traffic)
    user_reads = []

    class Request:
        app = None
        META = {SALEOR_AUTH_HEADER: "token"}

        @property
        def user(self):
            user_reads.append(True)
            raise InvalidTokenError("Invalid token.")

    # when
    blocked = is_storefront_traffic_blocked(Request())

    # then
    assert blocked is expected_blocked
    # Without this the expected result could also be reached by never reading
    # `.user`, leaving the InvalidTokenError branch untested.
    assert len(user_reads) == expected_user_reads


def test_unexpected_user_object_is_not_privileged(site_settings):
    # given
    _set_allow_storefront_traffic(site_settings, False)
    request = _make_request(app=None, user=object(), authenticated=True)

    # when / then
    with pytest.warns(UserWarning, match="An invalid user object was found"):
        assert is_storefront_traffic_blocked(request) is True


def test_cache_key_uses_site_id_when_configured():
    # given
    site_id = 7
    request = SimpleNamespace(get_host=lambda: "ignored.example.com")

    # when / then: the host is irrelevant, the configured site wins
    with override_settings(SITE_ID=site_id):
        cache_key = _get_allow_storefront_traffic_cache_key(request)
    assert cache_key == f"allow_storefront_traffic:{site_id}"


def test_cache_key_falls_back_to_host_without_site_id():
    # given: a multi-tenant deployment serving several sites from one process
    host = "tenant.example.com"
    request = SimpleNamespace(get_host=lambda: host)

    # when
    with override_settings(SITE_ID=None):
        cache_key = _get_allow_storefront_traffic_cache_key(request)

    # then
    assert cache_key == f"allow_storefront_traffic:{host}"


def test_cache_key_without_site_id_and_without_request():
    # when / then
    with (
        override_settings(SITE_ID=None),
        pytest.raises(ImproperlyConfigured) as exc_info,
    ):
        _get_allow_storefront_traffic_cache_key(None)
    assert str(exc_info.value) == (
        "Without settings.SITE_ID the site can only be identified by the request "
        "host, so a request is required to namespace the storefront traffic cache."
    )
