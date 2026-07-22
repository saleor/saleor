import pytest

from .storefront_traffic import set_allow_storefront_traffic_cache


@pytest.fixture(autouse=True)
def _warm_storefront_traffic_cache():
    """Keep the storefront-traffic guard from adding a DB query per request.

    ``is_storefront_traffic_blocked`` lazily loads the shop setting and caches
    it. In production the cache is warm, so the guard performs no DB query. Warm
    it here as well so query-count benchmarks measure the steady state and stay
    deterministic regardless of test ordering.

    Tests that exercise the blocking path (e.g. ``storefront_traffic_disabled``)
    explicitly clear/override the cache after this autouse fixture runs, so they
    are unaffected.
    """
    set_allow_storefront_traffic_cache(True)
