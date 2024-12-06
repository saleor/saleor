import datetime

import pytest
from freezegun import freeze_time

from saleor.webhook.transport.synchronous.circuit_breaker.storage import InMemoryStorage

APP_ID = 1
NAME = "total"
NOW = 1726215980
TTL_SECONDS = 60


@pytest.fixture
def storage():
    return InMemoryStorage()


def test_update_open(storage):
    assert storage.last_open(APP_ID) == 0

    storage.update_open(APP_ID, 100)
    assert storage.last_open(APP_ID) == 100

    storage.update_open(APP_ID, 0)
    assert storage.last_open(APP_ID) == 0


def test_register_event_returning_count(storage):
    with freeze_time(datetime.datetime.fromtimestamp(NOW, tz=datetime.UTC)):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 1

    with freeze_time(
        datetime.datetime.fromtimestamp(NOW + TTL_SECONDS - 1, tz=datetime.UTC)
    ):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 2

    with freeze_time(
        datetime.datetime.fromtimestamp(NOW + TTL_SECONDS, tz=datetime.UTC)
    ):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 2


def test_clear_state_for_app(storage):
    # given
    storage.update_open(APP_ID, 100)
    assert storage._last_open == {APP_ID: 100}

    # when
    storage.clear_state_for_app(APP_ID)

    # then
    assert storage._last_open == {}


def test_clear_state_for_app_missing_id(storage):
    # given
    storage.update_open(APP_ID, 100)
    assert storage._last_open == {APP_ID: 100}

    # when
    storage.clear_state_for_app(9999)

    # then
    assert storage._last_open == {APP_ID: 100}
