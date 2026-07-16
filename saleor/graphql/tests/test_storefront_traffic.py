from types import SimpleNamespace

import jwt
import pytest
from django.contrib.sites.models import Site

from saleor.graphql.storefront_traffic import is_storefront_traffic_blocked


def _set_allow_storefront_traffic(site_settings, allowed):
    site_settings.allow_storefront_traffic = allowed
    site_settings.save(update_fields=["allow_storefront_traffic"])
    # get_current() reads a process-global cache; refresh it.
    Site.objects.clear_cache()


@pytest.fixture(autouse=True)
def _clear_site_cache():
    # Guard against a cached Site leaking between tests in this module.
    Site.objects.clear_cache()
    yield
    Site.objects.clear_cache()


def test_blocks_anonymous_request_when_disabled(site_settings):
    # given
    _set_allow_storefront_traffic(site_settings, False)
    request = SimpleNamespace(app=None, user=None)

    # when / then
    assert is_storefront_traffic_blocked(request) is True


def test_allows_anonymous_request_when_enabled(site_settings):
    # given
    _set_allow_storefront_traffic(site_settings, True)
    request = SimpleNamespace(app=None, user=None)

    # when / then
    assert is_storefront_traffic_blocked(request) is False


def test_allows_app_request_when_disabled(site_settings, app):
    # given: an app is always allowed, regardless of the flag
    _set_allow_storefront_traffic(site_settings, False)
    request = SimpleNamespace(app=app, user=None)

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
    req = SimpleNamespace(app=None, user=user)

    # when / then
    assert is_storefront_traffic_blocked(req) is expected_blocked


def test_missing_principal_attributes_are_treated_as_storefront(site_settings):
    # given: a request object without app/user attributes at all
    _set_allow_storefront_traffic(site_settings, False)
    request = SimpleNamespace()

    # when / then
    assert is_storefront_traffic_blocked(request) is True


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

        @property
        def user(self):
            raise jwt.InvalidTokenError("Invalid token.")

    # when / then
    assert is_storefront_traffic_blocked(Request()) is expected_blocked
