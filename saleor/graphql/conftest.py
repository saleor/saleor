import pytest
from django.contrib.sites.models import Site

from .storefront_traffic import set_allow_storefront_traffic_cache


@pytest.fixture(autouse=True)
def _warm_storefront_traffic_cache():
    """Keep the storefront-traffic guard from adding DB queries per request.

    ``is_storefront_traffic_blocked`` resolves the current site and lazily loads the
    shop setting, caching both. In production those caches are warm, so the guard
    performs no DB query. Warm them here as well so query-count benchmarks measure
    the steady state and stay deterministic regardless of test ordering — a test must
    never assume either cache is cold.

    Tests that exercise the blocking path (e.g. ``storefront_traffic_disabled``)
    explicitly clear/override the cache after this autouse fixture runs, so they
    are unaffected.
    """
    Site.objects.get_current()
    set_allow_storefront_traffic_cache(True)
