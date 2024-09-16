from datetime import datetime

import fakeredis
import pytest
from freezegun import freeze_time

from saleor.webhook.transport.synchronous.circuit_breaker.storage import RedisStorage


@pytest.fixture
def storage():
    return RedisStorage(client=fakeredis.FakeRedis())


def test_update_open(storage):
    app_id = 1

    assert storage.last_open(app_id) == 0

    storage.update_open(app_id, 100)
    assert storage.last_open(app_id) == 100

    storage.update_open(app_id, 0)
    assert storage.last_open(app_id) == 0


def test_register_event_returning_count(storage):
    key = "foo"
    ttl_seconds = 60
    now = 1726215980

    with freeze_time(datetime.fromtimestamp(now)):
        assert storage.register_event_returning_count(key, ttl_seconds) == 1

    with freeze_time(datetime.fromtimestamp(now + ttl_seconds - 1)):
        assert storage.register_event_returning_count(key, ttl_seconds) == 2

    with freeze_time(datetime.fromtimestamp(now + ttl_seconds)):
        assert storage.register_event_returning_count(key, ttl_seconds) == 2
