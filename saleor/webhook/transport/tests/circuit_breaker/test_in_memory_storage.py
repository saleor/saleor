from datetime import datetime

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
    with freeze_time(datetime.fromtimestamp(NOW)):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 1

    with freeze_time(datetime.fromtimestamp(NOW + TTL_SECONDS - 1)):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 2

    with freeze_time(datetime.fromtimestamp(NOW + TTL_SECONDS)):
        assert storage.register_event_returning_count(APP_ID, NAME, TTL_SECONDS) == 2
