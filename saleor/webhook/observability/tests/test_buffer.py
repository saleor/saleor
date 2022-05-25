import pytest

from ..buffers import RedisBuffer, buffer_factory, get_buffer
from ..exceptions import ConnectionNotConfigured
from ..tests.conftest import BATCH_SIZE, KEY, MAX_SIZE


def test_buffer_factory(redis_server, settings):
    buffer = buffer_factory(KEY)
    assert isinstance(buffer, RedisBuffer)
    assert buffer.max_size == settings.OBSERVABILITY_BUFFER_SIZE_LIMIT
    assert buffer.batch_size == settings.OBSERVABILITY_BUFFER_BATCH_SIZE


def test_get_buffer_when_no_configured(settings):
    settings.OBSERVABILITY_BROKER_URL = None
    with pytest.raises(ConnectionNotConfigured):
        get_buffer(KEY)


def test_get_buffer(redis_server, settings):
    buffer = get_buffer(KEY)
    buffer_bis = get_buffer(KEY)
    assert id(buffer) == id(buffer_bis)
    assert buffer.broker_url == settings.OBSERVABILITY_BROKER_URL
    assert buffer.max_size == settings.OBSERVABILITY_BUFFER_SIZE_LIMIT
    assert buffer.batch_size == settings.OBSERVABILITY_BUFFER_BATCH_SIZE


def test_in_batches(buffer):
    assert buffer.in_batches(BATCH_SIZE + BATCH_SIZE // 2) == 2


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


def test_pop_events_get_size(buffer):
    events = [{"event": f"data{i}"} for i in range(MAX_SIZE)]
    buffer.put_events(events)
    popped_events, size = buffer.pop_events_get_size()
    assert len(popped_events) == BATCH_SIZE
    assert popped_events == events[:BATCH_SIZE]
    assert size == MAX_SIZE - BATCH_SIZE
    assert buffer.size() == size


def test_clear(buffer):
    events = [{"event": "data"}] * 2
    buffer.put_events(events)
    assert buffer.size() == 2
    assert buffer.clear() == 2
    assert buffer.size() == 0
