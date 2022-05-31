import time
from datetime import timedelta
from functools import partial
from unittest.mock import call, patch

import pytest
from redis.exceptions import RedisError

from .. import worker
from .conftest import KEY, MAX_SIZE

BATCH_SIZE = 10
QUEUE_SIZE = worker.BackgroundWorker.queue_size(BATCH_SIZE)
REPORT_PERIOD = timedelta(seconds=0.01)
JOIN_TIMEOUT = REPORT_PERIOD.total_seconds() * 2


@pytest.fixture
def mock_buffer_put_multi_key_events():
    target = "saleor.webhook.observability.worker.buffer_put_multi_key_events"
    with patch(target) as mock:
        yield mock


@pytest.fixture
def init_worker(settings, mock_buffer_put_multi_key_events):
    settings.OBSERVABILITY_BUFFER_BATCH_SIZE = BATCH_SIZE
    settings.OBSERVABILITY_REPORT_PERIOD = REPORT_PERIOD
    worker.init()
    yield
    worker.shutdown()


@patch("saleor.webhook.observability.worker.get_buffer")
def test_buffer_put_multi_key_events(mock_get_buffer, buffer):
    mock_get_buffer.return_value = buffer
    events = {KEY: ["payload"], "buffer_b": ["payload"]}

    assert worker.buffer_put_multi_key_events(events) is True


@patch("saleor.webhook.observability.worker.get_buffer")
def test_buffer_put_multi_key_events_when_buffer_is_full(mock_get_buffer, buffer):
    mock_get_buffer.return_value = buffer
    for _ in range(MAX_SIZE):
        buffer.put_event("payload")
    assert buffer.size() == MAX_SIZE
    events = {KEY: ["payload"], "buffer_b": ["payload"]}

    assert worker.buffer_put_multi_key_events(events) is False


def test_put_event_when_worker_not_initialized():
    worker.shutdown()

    assert worker.put_event("buffer", lambda: "payload") is False
    assert worker.queue_join(JOIN_TIMEOUT) is False


def test_background_worker(init_worker, mock_buffer_put_multi_key_events):
    payload = "buffer_a", "payload"

    worker.put_event(KEY, lambda: payload)

    assert worker.queue_join(JOIN_TIMEOUT) is True
    mock_buffer_put_multi_key_events.assert_called_once_with({KEY: [payload]})


def test_background_worker_put_multiple_events(
    init_worker, mock_buffer_put_multi_key_events
):
    payload = "payload-{}"
    for i in range(BATCH_SIZE + 1):
        worker.put_event(KEY, partial(payload.format, i))

    assert worker.queue_join(JOIN_TIMEOUT) is True
    mock_buffer_put_multi_key_events.assert_has_calls(
        [
            call({KEY: [payload.format(i) for i in range(BATCH_SIZE)]}),
            call({KEY: [payload.format(BATCH_SIZE)]}),
        ]
    )


def test_background_worker_put_events_multi_buffer(
    init_worker, mock_buffer_put_multi_key_events
):
    buffer_a, buffer_b, payload = "buffer_a", "buffer_b", "payload-{}"
    for i in range(BATCH_SIZE // 2):
        worker.put_event(buffer_a, partial(payload.format, i))
        worker.put_event(buffer_b, partial(payload.format, i))

    assert worker.queue_join(JOIN_TIMEOUT) is True
    mock_buffer_put_multi_key_events.assert_called_once_with(
        {
            buffer_a: [payload.format(i) for i in range(BATCH_SIZE // 2)],
            buffer_b: [payload.format(i) for i in range(BATCH_SIZE // 2)],
        }
    )


def test_background_worker_when_queue_is_full(
    init_worker, mock_buffer_put_multi_key_events
):
    for _ in range(QUEUE_SIZE):
        worker.put_event(KEY, lambda: "payload")

    assert worker.put_event(KEY, lambda: "payload") is False
    mock_buffer_put_multi_key_events.assert_called()


def test_background_worker_exception_raised_while_put_to_buffer_dont_stop_worker(
    init_worker, mock_buffer_put_multi_key_events
):
    put_buffer_side_effects = [RedisError, True]
    mock_buffer_put_multi_key_events.side_effect = put_buffer_side_effects
    for _ in range(len(put_buffer_side_effects)):
        for _ in range(BATCH_SIZE):
            worker.put_event(KEY, lambda: "payload")
        assert worker.queue_join(JOIN_TIMEOUT) is True

    assert mock_buffer_put_multi_key_events.call_count == len(put_buffer_side_effects)


def test_background_worker_when_generate_payload_raises_exception(
    init_worker, mock_buffer_put_multi_key_events
):
    payload = "payload-{}"
    worker.put_event(KEY, lambda: 1 / 0)
    for i in range(BATCH_SIZE):
        worker.put_event(KEY, partial(payload.format, i))

    assert worker.queue_join(JOIN_TIMEOUT) is True
    mock_buffer_put_multi_key_events.assert_called_once_with(
        {KEY: [payload.format(i) for i in range(BATCH_SIZE)]}
    )


def test_background_worker_shutdown(init_worker, mock_buffer_put_multi_key_events):
    payload = "payload-{}"
    for i in range(BATCH_SIZE):
        worker.put_event(KEY, partial(payload.format, i))
    worker.shutdown()
    mock_buffer_put_multi_key_events.assert_called_once_with(
        {KEY: [payload.format(i) for i in range(BATCH_SIZE)]}
    )


def test_background_worker_shutdown_when_queue_full(
    init_worker, mock_buffer_put_multi_key_events
):
    for _ in range(QUEUE_SIZE):
        worker.put_event(KEY, lambda: "payload")
    worker.shutdown()
    mock_buffer_put_multi_key_events.assert_called()


def test_background_worker_failed_flush_on_shutdown(
    init_worker, mock_buffer_put_multi_key_events
):
    def generate_payload():
        time.sleep(JOIN_TIMEOUT * 2)
        return "payload"

    worker.put_event(KEY, generate_payload)
    worker.shutdown(JOIN_TIMEOUT)
    mock_buffer_put_multi_key_events.assert_not_called()
