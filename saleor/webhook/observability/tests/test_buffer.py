from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ..buffers import RedisBuffer, get_buffer
from ..exceptions import ConnectionNotConfigured
from ..tests.conftest import BATCH_SIZE, BROKER_URL_HOST, KEY, MAX_SIZE


def test_get_buffer(redis_server, settings):
    buffer = get_buffer(KEY)
    assert isinstance(buffer, RedisBuffer)
    assert buffer.max_size == settings.OBSERVABILITY_BUFFER_SIZE_LIMIT
    assert buffer.batch_size == settings.OBSERVABILITY_BUFFER_BATCH_SIZE


def test_get_buffer_with_no_config(settings):
    settings.OBSERVABILITY_BROKER_URL = None
    with pytest.raises(ConnectionNotConfigured):
        get_buffer(KEY)


def test_get_connection_pool(buffer):
    pool = buffer.get_connection_pool()
    assert pool.connection_kwargs["host"] == BROKER_URL_HOST
    assert pool.connection_kwargs["socket_timeout"] == buffer.connection_timeout
    assert (
        pool.connection_kwargs["socket_connect_timeout"]
        == buffer._socket_connect_timeout
    )
    assert pool.connection_kwargs["client_name"] == buffer._client_name


def test_get_or_create_connection_pool(redis_server):
    buffer = get_buffer(KEY)
    pool_a = buffer.get_or_create_connection_pool()
    pool_b = buffer.get_or_create_connection_pool()
    assert pool_a == pool_b


def test_in_batches(buffer):
    assert buffer.in_batches(BATCH_SIZE + BATCH_SIZE // 2) == 2


def test_put_event(buffer, event_data):
    dropped = buffer.put_event(event_data)
    assert buffer.size() == 1
    assert dropped == 0


def test_buffer_put_events_max_size(buffer, event_data):
    for i in range(MAX_SIZE * 2):
        buffer.put_event(event_data)
    assert buffer.size() == MAX_SIZE


def test_put_events(buffer, event_data):
    events = [event_data] * 2
    dropped = buffer.put_events(events)
    assert buffer.size() == 2
    assert dropped == 0


def test_put_events_max_size(buffer, event_data):
    events = [event_data] * MAX_SIZE * 2
    dropped = buffer.put_events(events)
    assert buffer.size() == MAX_SIZE
    assert dropped == MAX_SIZE


def test_buffer_drops_events_when_put_events(buffer, event_data):
    events = [event_data] * MAX_SIZE
    buffer.put_events(events)
    dropped = buffer.put_events(events)
    assert dropped == MAX_SIZE
    assert buffer.size() == MAX_SIZE


def test_put_multi_key_events(patch_connection_pool, event_data):
    key_a, events_a = "buffer_a", [event_data] * 2
    key_b, events_b = "buffer_b", [event_data] * MAX_SIZE
    key_c, events_c = "buffer_c", [event_data] * MAX_SIZE * 2
    buffer_a, buffer_b, buffer_c = (
        get_buffer(key_a),
        get_buffer(key_b),
        get_buffer(key_c),
    )
    dropped = buffer_a.put_multi_key_events(
        {key_a: events_a, key_b: events_b, key_c: events_c}
    )
    assert buffer_a.size() == 2
    assert buffer_b.size() == MAX_SIZE
    assert buffer_c.size() == MAX_SIZE
    assert dropped == {key_a: 0, key_b: 0, key_c: MAX_SIZE}


def test_put_multi_key_events_when_buffer_full(patch_connection_pool, event_data):
    max_events = [event_data] * MAX_SIZE
    key_a, events_a = "buffer_a", [event_data] * 2
    key_b, events_b = "buffer_b", [event_data] * MAX_SIZE
    key_c, events_c = "buffer_c", [event_data] * MAX_SIZE * 2
    buffer_a = get_buffer(key_a)
    buffer_a.put_multi_key_events(
        {key_a: max_events, key_b: max_events, key_c: max_events}
    )

    dropped = buffer_a.put_multi_key_events(
        {key_a: events_a, key_b: events_b, key_c: events_c}
    )
    assert dropped == {key_a: 2, key_b: MAX_SIZE, key_c: MAX_SIZE * 2}


def test_pop_event(buffer, event_data):
    buffer.put_event(event_data)
    popped_event = buffer.pop_event()
    assert id(event_data) != id(popped_event)
    assert event_data == popped_event
    assert buffer.size() == 0
    assert buffer.pop_event() is None


def test_pop_events(buffer, event_data):
    events = [f"event-data-{i}".encode() for i in range(MAX_SIZE)]
    buffer.put_events(events)
    popped_events = buffer.pop_events()
    assert len(popped_events) == BATCH_SIZE
    assert popped_events == events[:BATCH_SIZE]
    assert buffer.size() == MAX_SIZE - BATCH_SIZE


def test_pop_events_get_size(buffer):
    events = [f"event-data-{i}".encode() for i in range(MAX_SIZE)]
    buffer.put_events(events)
    popped_events, size = buffer.pop_events_get_size()
    assert len(popped_events) == BATCH_SIZE
    assert popped_events == events[:BATCH_SIZE]
    assert size == MAX_SIZE - BATCH_SIZE
    assert buffer.size() == size


def test_clear(buffer, event_data):
    events = [event_data] * 2
    buffer.put_events(events)
    assert buffer.size() == 2
    assert buffer.clear() == 2
    assert buffer.size() == 0


def test_pop_expired_events(buffer):
    push_time = timezone.now()
    with freeze_time(push_time):
        events = [f"event-data-{i}".encode() for i in range(MAX_SIZE)]
        buffer.put_events(events)
    with freeze_time(push_time + timedelta(seconds=buffer.timeout + 1)):
        popped_events = buffer.pop_events()
    assert popped_events == []
