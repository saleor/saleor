from datetime import datetime
from unittest.mock import Mock, patch

import fakeredis
import pytest
from django.core.exceptions import ImproperlyConfigured
from freezegun import freeze_time
from redis.client import Pipeline

from saleor.webhook.transport.synchronous.circuit_breaker.storage import RedisStorage

APP_ID = 1
NAME = "total"
NOW = 1726215980
TTL_SECONDS = 60


@pytest.fixture
def storage():
    server = fakeredis.FakeServer()
    server.connected = True

    return RedisStorage(client=fakeredis.FakeRedis(server=server))


@pytest.fixture
def not_connected_storage():
    server = fakeredis.FakeServer()
    server.connected = False

    return RedisStorage(client=fakeredis.FakeRedis(server=server))


def test_update_open(storage):
    assert storage.last_open(APP_ID) == 0

    storage.update_open(APP_ID, 100)
    assert storage.last_open(APP_ID) == 100

    storage.update_open(APP_ID, 0)
    assert storage.last_open(APP_ID) == 0


def test_register_event_returning_count(storage):
    with freeze_time(datetime.fromtimestamp(NOW)):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 1

    with freeze_time(datetime.fromtimestamp(NOW + TTL_SECONDS - 1)):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 2

    with freeze_time(datetime.fromtimestamp(NOW + TTL_SECONDS)):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 2


def test_last_open_does_not_crash_on_redis_error(not_connected_storage):
    assert not_connected_storage.last_open(APP_ID) == 0


def test_update_open_does_not_crash_on_redis_error(not_connected_storage):
    not_connected_storage.update_open(APP_ID, 100)
    assert not_connected_storage.last_open(APP_ID) == 0


def test_register_event_returning_count_does_not_crash_on_redis_error(
    not_connected_storage,
):
    assert (
        not_connected_storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS)
        == 0
    )


def test_register_event_returning_count_does_not_crash_on_empty_response(storage):
    with patch.object(Pipeline, "execute", Mock(return_value=[])):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 0


def test_storage_raises_on_non_redis_cache_url(settings):
    settings.CACHE_URL = "definitelynotredis://localhost:7000"

    with pytest.raises(ImproperlyConfigured):
        RedisStorage()
