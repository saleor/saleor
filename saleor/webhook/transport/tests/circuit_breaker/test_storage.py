import pytest
from freezegun import freeze_time

from saleor.webhook.transport.synchronous.circuit_breaker.storage import InMemoryStorage


@pytest.fixture
def storage():
    return InMemoryStorage()


def test_update_open(storage):
    app_id = 1

    assert app_id not in storage._last_open
    assert storage.last_open(app_id) == 0

    storage.update_open(app_id, 100)
    assert storage.last_open(app_id) == 100

    storage.update_open(app_id, 0)
    assert storage.last_open(app_id) == 0


def test_register_event_returning_count(storage):
    app_id = 1
    failures_key = f"{app_id}-failure"
    ttl_seconds = 60

    with freeze_time("2012-01-14 11:00:00"):
        assert storage.register_event_returning_count(failures_key, ttl_seconds) == 1

    with freeze_time("2012-01-14 11:00:30"):
        assert storage.register_event_returning_count(failures_key, ttl_seconds) == 2

    with freeze_time("2012-01-14 11:01:01"):
        assert storage.register_event_returning_count(failures_key, ttl_seconds) == 2
