from unittest.mock import patch

import fakeredis
import pytest
from redis import ConnectionPool

from ..buffers import RedisBuffer, buffer_factory, get_buffer
from ..exceptions import ConnectionNotConfigured

BROKER_URL = "redis://fake-redis"
KEY, MAX_SIZE, BATCH_SIZE = "observability_buffer", 10, 5


@pytest.fixture
def redis_server(settings):
    settings.OBSERVABILITY_BROKER_URL = BROKER_URL
    settings.OBSERVABILITY_BUFFER_SIZE_LIMIT = MAX_SIZE
    settings.OBSERVABILITY_BUFFER_BATCH_SIZE = BATCH_SIZE
    server = fakeredis.FakeServer()
    server.connected = True
    yield server


@pytest.fixture
def patch_redis(redis_server):
    with patch(
        "saleor.webhook.observability.buffers.RedisBuffer.get_connection_pool",
        lambda x: ConnectionPool(
            connection_class=fakeredis.FakeConnection, server=redis_server
        ),
    ):
        yield


@pytest.fixture
def buffer(patch_redis):
    buffer = buffer_factory(BROKER_URL, KEY, max_size=MAX_SIZE, batch_size=BATCH_SIZE)
    yield buffer
    buffer.client.flushall()


def test_buffer_factory():
    max_size, batch_size = 10, 10
    buffer = buffer_factory(BROKER_URL, KEY, max_size=max_size, batch_size=batch_size)
    assert isinstance(buffer, RedisBuffer)
    assert (buffer.max_size, buffer.batch_size) == (max_size, batch_size)


def test_get_buffer_when_no_configured(settings):
    settings.OBSERVABILITY_BROKER_URL = None
    with pytest.raises(ConnectionNotConfigured):
        get_buffer(KEY)


def test_get_buffer(settings):
    settings.OBSERVABILITY_BROKER_URL = "redis://fake-redis"
    buffer = get_buffer(KEY)
    buffer_bis = get_buffer(KEY)
    assert id(buffer) == id(buffer_bis)
    assert buffer.broker_url == settings.OBSERVABILITY_BROKER_URL
    assert buffer.max_size == settings.OBSERVABILITY_BUFFER_SIZE_LIMIT
    assert buffer.batch_size == settings.OBSERVABILITY_BUFFER_BATCH_SIZE


def test_buffer_put_events(buffer):
    event = {"event": "data"}
    buffer.put_event(event)
    assert buffer.size() == 1


def test_buffer_put_events_max_size(buffer):
    event = {"event": "data"}
    for i in range(MAX_SIZE * 2):
        buffer.put_event(event)
    assert buffer.size() == MAX_SIZE


def test_put_events(buffer):
    events = [{"event": "data"}] * 2
    buffer.put_events(events)
    assert buffer.size() == 2


def test_put_events_max_size(buffer):
    events = [{"event": "data"}] * MAX_SIZE * 2
    buffer.put_events(events)
    assert buffer.size() == MAX_SIZE


def test_put_multi_key_events(patch_redis):
    key_a, events_a = "buffer_a", [{"event": "data"}] * 2
    key_b, events_b = "buffer_b", [{"event": "data"}] * MAX_SIZE
    key_c, events_c = "buffer_c", [{"event": "data"}] * MAX_SIZE * 2
    buffer_a, buffer_b, buffer_c = (
        get_buffer(key_a),
        get_buffer(key_b),
        get_buffer(key_c),
    )
    buffer_a.put_multi_key_events({key_a: events_a, key_b: events_b, key_c: events_c})
    assert buffer_a.size() == 2
    assert buffer_b.size() == MAX_SIZE
    assert buffer_c.size() == MAX_SIZE


def test_pop_event(buffer):
    event = "buffer", {"event": "data"}
    buffer.put_event(event)
    popped_event = buffer.pop_event()
    assert id(event) != id(popped_event)
    assert event == popped_event
    assert buffer.size() == 0
    assert buffer.pop_event() is None


def test_pop_events(buffer):
    events = [{"event": f"data{i}"} for i in range(MAX_SIZE)]
    buffer.put_events(events)
    popped_events = buffer.pop_events()
    assert len(popped_events) == BATCH_SIZE
    assert popped_events == events[:BATCH_SIZE]
    assert buffer.size() == MAX_SIZE - BATCH_SIZE


def test_clear(buffer):
    events = [{"event": "data"}] * 2
    buffer.put_events(events)
    assert buffer.size() == 2
    assert buffer.clear() == 2
    assert buffer.size() == 0
