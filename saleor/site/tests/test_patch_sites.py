import pytest
from django.conf import settings as django_settings
from django.contrib.sites.models import Site
from django.db import connections
from django.test import RequestFactory

from .. import patch_sites


def _replica_connection():
    """Return the connection the patched site lookups query."""
    return connections[django_settings.DATABASE_CONNECTION_REPLICA_NAME]


@pytest.mark.parametrize(
    ("_case", "use_request_host"),
    [
        ("site resolved by SITE_ID", False),
        ("site resolved by request host", True),
    ],
)
def test_get_current_queries_database_without_holding_lock(
    _case, use_request_host, site_settings, settings
):
    # given
    site = site_settings.site
    request = None
    if use_request_host:
        settings.SITE_ID = None
        request = RequestFactory().get("/", HTTP_HOST=site.domain)
    Site.objects.clear_cache()

    lock_held_during_queries = []

    def record_lock_state(execute, sql, params, many, context):
        lock_held_during_queries.append(patch_sites.lock.locked())
        return execute(sql, params, many, context)

    # when
    with _replica_connection().execute_wrapper(record_lock_state):
        result = Site.objects.get_current(request)

    # then
    assert result == site
    assert result.settings == site_settings
    # One query for the site and one for its prefetched settings.
    assert lock_held_during_queries == [False, False]


def test_get_current_does_not_cache_site_fetched_before_cache_clear(site_settings):
    # given
    site = site_settings.site
    Site.objects.clear_cache()

    def clear_cache_during_query(execute, sql, params, many, context):
        # Simulate another thread clearing the cache while the site is fetched.
        # Clearing needs the lock, so only do it when the lock is free.
        if not patch_sites.lock.locked():
            Site.objects.clear_cache()
        return execute(sql, params, many, context)

    # when
    with _replica_connection().execute_wrapper(clear_cache_during_query):
        result = Site.objects.get_current()

    # then
    assert result == site
    assert patch_sites.THREADED_SITE_CACHE == {}
