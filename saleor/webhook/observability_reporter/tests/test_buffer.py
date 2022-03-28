import json
from unittest.mock import patch

import pytest
from kombu.exceptions import ChannelError
from kombu.exceptions import ConnectionError as KombuConnectionError
from kombu.exceptions import KombuError

from ..buffer import (
    CACHE_KEY,
    FullObservabilityBuffer,
    ObservabilityBuffer,
    ObservabilityConnectionError,
    ObservabilityKombuError,
    buffer_size,
    get_events,
    observability_buffer,
    observability_connection,
    put_event,
)
from .conftest import TESTS_TIMEOUT, fill_buffer


def _make_key(x, prefix="key_prefix"):
    return f"{prefix}:1:{x}"


def test_clear_buffer(memory_broker):
    with ObservabilityBuffer(memory_broker) as buffer:
        fill_buffer(buffer, 10)
        assert len(buffer) == 10
        buffer.clear()
        assert len(buffer) == 0


def test_buffer_if_durable(memory_broker):
    with ObservabilityBuffer(memory_broker) as buffer:
        buffer.put_event(json.dumps({"test": "data"}))
        assert len(buffer) == 1
    with ObservabilityBuffer(memory_broker, batch_size=1) as buffer:
        assert len(buffer) == 1
        buffer.get_events()
        assert len(buffer) == 0


@patch("saleor.webhook.observability_reporter.buffer.cache.make_key")
def test_observability_buffer_repr_contain_cache_key(mock_make_key, memory_broker):
    mock_make_key.side_effect = _make_key
    with ObservabilityBuffer(memory_broker) as buffer:
        assert _make_key(CACHE_KEY) in repr(buffer)


@patch("saleor.webhook.observability_reporter.buffer.cache.make_key")
def test_multiple_observability_buffers_on_the_same_broker(
    mock_make_key, memory_broker
):
    buffer_a_prefix, buffer_a_size = "first_prefix", 5
    buffer_b_prefix, buffer_b_size = "second_prefix", 3
    mock_make_key.side_effect = lambda x: _make_key(x, prefix=buffer_a_prefix)
    with ObservabilityBuffer(memory_broker) as buffer:
        fill_buffer(buffer, buffer_a_size)
        assert len(buffer) == buffer_a_size
    mock_make_key.side_effect = lambda x: _make_key(x, prefix=buffer_b_prefix)
    with ObservabilityBuffer(memory_broker) as buffer:
        fill_buffer(buffer, buffer_b_size)
        assert len(buffer) == buffer_b_size
    mock_make_key.side_effect = lambda x: _make_key(x, prefix=buffer_a_prefix)
    with ObservabilityBuffer(memory_broker) as buffer:
        assert len(buffer) == buffer_a_size


def test_buffer_size(memory_broker):
    with ObservabilityBuffer(memory_broker, batch_size=10) as buffer:
        fill_buffer(buffer, 11)
        assert len(buffer) == 11


def test_buffer_get_events(memory_broker):
    with ObservabilityBuffer(memory_broker, batch_size=20) as buffer:
        fill_buffer(buffer, 10)

        events = buffer.get_events(timeout=TESTS_TIMEOUT)

        assert len(events) == 10
        assert len(buffer) == 0


@patch("saleor.webhook.observability_reporter.buffer.SimpleQueue.qsize")
def test_buffer_size_when_queue_not_exists(mock_qsize, memory_broker):
    mock_qsize.side_effect = ChannelError
    with ObservabilityBuffer(memory_broker) as buffer:
        assert len(buffer) == 0


def test_buffer_json_deserialization(memory_broker):
    event = {"test": "data"}
    with ObservabilityBuffer(memory_broker) as buffer:
        buffer.put_event(json.dumps({"test": "data"}))
        assert buffer.get_events(timeout=TESTS_TIMEOUT)[0] == event


def test_buffer_max_size(memory_broker):
    with ObservabilityBuffer(memory_broker, max_size=10) as buffer:
        fill_buffer(buffer, 10)
        with pytest.raises(FullObservabilityBuffer):
            buffer.put_event(json.dumps({"skiped": "event"}))
        assert len(buffer) == 10


@pytest.mark.parametrize(
    "error,observability_error",
    [
        (KombuConnectionError, ObservabilityConnectionError),
        (KombuError, ObservabilityKombuError),
        (Exception, Exception),
    ],
)
@patch("saleor.webhook.observability_reporter.buffer.ObservabilityBuffer.put_event")
def test_observability_connection_catch_all_exceptions(
    mock_put, memory_broker, error, observability_error
):
    mock_put.side_effect = error
    with pytest.raises(observability_error):
        with observability_connection(memory_broker) as conn:
            with ObservabilityBuffer(conn) as buffer:
                buffer.put_event(json.dumps({"test": "data"}))


def test_get_buffer_loads_proper_settings(memory_broker_url, settings):
    settings.OBSERVABILITY_BROKER_URL = memory_broker_url
    settings.OBSERVABILITY_BUFFER_BATCH_SIZE = 3
    settings.OBSERVABILITY_BUFFER_SIZE_LIMIT = 5

    with observability_buffer() as buffer:
        assert buffer.batch_size == 3
        assert buffer.max_size == 5


def test_observability_buffer_put_event(memory_broker_url, memory_broker, settings):
    settings.OBSERVABILITY_BROKER_URL = memory_broker_url
    payload = {"test": "payload"}

    put_event(json.dumps(payload))

    with ObservabilityBuffer(memory_broker) as buffer:
        assert buffer.get_events(timeout=TESTS_TIMEOUT)[0] == payload


def test_observability_buffer_get_events(memory_broker_url, memory_broker, settings):
    settings.OBSERVABILITY_BROKER_URL = memory_broker_url
    with ObservabilityBuffer(memory_broker) as buffer:
        fill_buffer(buffer, 10)

    events = get_events(timeout=TESTS_TIMEOUT)

    assert len(events) == 10


def test_observability_buffer_size_in_batches(
    memory_broker_url, memory_broker, settings
):
    settings.OBSERVABILITY_BROKER_URL = memory_broker_url
    with ObservabilityBuffer(memory_broker) as buffer:
        fill_buffer(buffer, 11)

    assert buffer_size() == 11
