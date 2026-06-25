from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime

import pytest

from .....site.apps import SiteAppConfig
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import AnnouncementImportanceEnum
from ...types import Announcement

QUERY_GET_ANNOUNCEMENTS_BASIC = """
{
    shop {
        announcements {
            title
            messageHtml
        }
    }
}
"""

QUERY_GET_ANNOUNCEMENTS_FULL = """
{
    shop {
        announcements {
            createdAt
            updatedAt
            title
            messageHtml
            importance
            type
            extra
        }
    }
}
"""

DUMMY_TITLE = "Dummy Announcement"
DUMMY_DESCRIPTION = (
    "This is an example body. This supports <strong>HTML markup</strong>."
)

DUMMY_CREATED_AT = "2022-06-13T16:01:02.300000+00:00"
DUMMY_UPDATED_AT = "2022-06-14T17:04:05.600000+00:00"

# TODO: switch to frozendict once Saleor uses Python 3.15 (including child dicts)
DUMMY_ANNOUNCEMENT = {
    "created_at": datetime.fromisoformat(DUMMY_CREATED_AT),
    "updated_at": datetime.fromisoformat(DUMMY_UPDATED_AT),
    "title": DUMMY_TITLE,
    "message_html": DUMMY_DESCRIPTION,
    "importance": AnnouncementImportanceEnum.CRITICAL,
    "type": "OTHER",
    "extra": {"foo": "bar", "integer": 123},
}


def resolve_dummy_announcements() -> list[Announcement]:
    return [Announcement(**DUMMY_ANNOUNCEMENT)]


def resolve_dummy_announcements_with_empty_extra_dict() -> list[Announcement]:
    """Return a dummy announcement with ``extra`` empty."""

    announcement = {**DUMMY_ANNOUNCEMENT}  # shallow copy
    announcement["extra"] = {}

    return [Announcement(**announcement)]


def resolve_dummy_announcements_with_null_extra() -> list[Announcement]:
    """Return a dummy announcement with ``extra`` empty."""

    announcement = {**DUMMY_ANNOUNCEMENT}  # shallow copy
    announcement["extra"] = None

    return [Announcement(**announcement)]


@contextmanager
def use_dummy_announcements(
    settings,
    resolver_func: Callable[[], list[Announcement]] = resolve_dummy_announcements,
):
    """Set the announcement resolver to the given ``resolver_func``.

    Example usage:

    >>> def resolver():
    >>>     return []
    >>>
    >>> def test_foo(settings):
    >>>     with use_dummy_announcements(settings, resolver): ...
    """

    # Ensure there wasn't any cross-test leakage where a fixture or test
    # didn't reset the SiteAppConfig properly. If it raises an AssertionError,
    # then you should fix the leakage
    assert SiteAppConfig.announcements_resolver is None

    import_path = f"{resolver_func.__module__}.{resolver_func.__name__}"
    settings.SHOP_ANNOUNCEMENT_RESOLVER_IMPORT = import_path

    try:
        SiteAppConfig.setup_announcements()  # loads the new resolver
        yield
    finally:
        settings.SHOP_ANNOUNCEMENT_RESOLVER_IMPORT = None
        SiteAppConfig.announcements_resolver = None


@pytest.fixture(autouse=True)
def default_settings(settings):
    """Set the resolver to None, then reverts the changes during tear-down."""
    old_resolver = SiteAppConfig.announcements_resolver

    # Overrides the default resolver as it may potentially
    # be set by users thus causing our tests to fail because we
    # expect the value to be `None`
    settings.SHOP_ANNOUNCEMENT_RESOLVER_IMPORT = None
    SiteAppConfig.announcements_resolver = None

    yield

    SiteAppConfig.announcements_resolver = old_resolver


def test_cannot_get_announcements_when_not_staff(user_api_client):
    """Authenticated user are not authorized to get announcements when not a staff."""

    query = QUERY_GET_ANNOUNCEMENTS_BASIC
    response = user_api_client.post_graphql(query)
    assert_no_permission(response)


def test_cannot_get_announcements_when_anonymous(api_client):
    """Anonymous users are not authorized to get announcements."""

    query = QUERY_GET_ANNOUNCEMENTS_BASIC
    response = api_client.post_graphql(query)
    assert_no_permission(response)


def test_can_get_announcements_when_staff(staff_api_client, staff_user):
    """Staff users should be authorized to get announcements."""

    # Ensures that the staff has no permissions as we do not expect
    # the user to need any specific/given permissions.
    assert len(staff_user.effective_permissions) == 0, (
        "Expected the staff to not have any permission"
    )

    query = QUERY_GET_ANNOUNCEMENTS_BASIC
    content = get_graphql_content(staff_api_client.post_graphql(query))

    # Should return the announcements without any errors
    assert content["data"] == {"shop": {"announcements": []}}


def test_get_announcements_empty_when_unconfigured(staff_api_client):
    """Ensure announcements are empty when not configured.

    When ``settings.SHOP_ANNOUNCEMENT_RESOLVER_IMPORT`` is unset (``None``)
    (default value), then, ``shop { announcements {...} }`` should return an empty list.
    """

    response = staff_api_client.post_graphql(QUERY_GET_ANNOUNCEMENTS_BASIC)
    content = get_graphql_content(response)
    assert content["data"] == {"shop": {"announcements": []}}


def test_get_announcements_uses_custom_resolver(settings, staff_api_client):
    """Ensure announcements are fetched from the custom resolver when configured.

    When ``settings.SHOP_ANNOUNCEMENT_RESOLVER_IMPORT`` is configured (``!= None``),
    then, Saleor should return the announcements from that resolver.
    """

    with use_dummy_announcements(settings):
        response = staff_api_client.post_graphql(QUERY_GET_ANNOUNCEMENTS_FULL)

    content = get_graphql_content(response)
    assert content["data"] == {
        "shop": {
            "announcements": [
                {
                    "createdAt": DUMMY_CREATED_AT,
                    "updatedAt": DUMMY_UPDATED_AT,
                    "title": DUMMY_TITLE,
                    "messageHtml": DUMMY_DESCRIPTION,
                    "importance": "CRITICAL",
                    "type": "OTHER",
                    "extra": {
                        "foo": "bar",
                        "integer": 123,  # should have allowed the non-str type
                    },
                }
            ]
        }
    }


def test_get_announcements_allows_empty_extra_dict(settings, staff_api_client):
    """Ensure the ``extra`` field can be empty (``{}``)."""

    with use_dummy_announcements(
        settings,
        resolve_dummy_announcements_with_empty_extra_dict,
    ):
        response = staff_api_client.post_graphql(
            QUERY_GET_ANNOUNCEMENTS_FULL,
        )

    content = get_graphql_content(response)
    assert content["data"] == {
        "shop": {
            "announcements": [
                {
                    "createdAt": DUMMY_CREATED_AT,
                    "updatedAt": DUMMY_UPDATED_AT,
                    "title": DUMMY_TITLE,
                    "messageHtml": DUMMY_DESCRIPTION,
                    "importance": "CRITICAL",
                    "type": "OTHER",
                    "extra": {},  # Should have allowed the empty dict
                }
            ]
        }
    }


def test_get_announcements_does_not_allow_null_extra(settings, staff_api_client):
    """Ensure the ``extra`` field cannot be null.

    ``extra=None`` shouldn't be allowed, instead it should be an empty dict.
    This should cause Saleor to reject the value (crash).
    """

    with use_dummy_announcements(
        settings,
        resolve_dummy_announcements_with_null_extra,
    ):
        response = staff_api_client.post_graphql(
            QUERY_GET_ANNOUNCEMENTS_FULL,
        )

    response = get_graphql_content_from_response(response)
    errors = response.get("errors", [])
    assert len(errors) == 1
    assert (
        errors[0]["message"]
        == "Cannot return null for non-nullable field Announcement.extra."
    )
