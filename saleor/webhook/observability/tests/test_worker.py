from datetime import timedelta
from functools import partial
from unittest.mock import patch

import pytest

from .. import worker
from .conftest import KEY, MAX_SIZE

BATCH_SIZE = 10
REPORT_PERIOD = timedelta(seconds=1)


@pytest.fixture
def worker_settings(settings):
    settings.OBSERVABILITY_BUFFER_BATCH_SIZE = BATCH_SIZE
    settings.OBSERVABILITY_REPORT_PERIOD = REPORT_PERIOD


@pytest.fixture
def init(worker_settings):
    worker.init()


@pytest.fixture
def init_no_timeout(settings, worker_settings):
    settings.OBSERVABILITY_REPORT_PERIOD = timedelta(seconds=0)
    worker.init()


def test_init(init):
    assert isinstance(worker._worker, worker.BackgroundWorker)


def test_put_event_when_worker_not_initialized():
    worker.shutdown_worker()
    assert worker.put_event("buffer", "payload") is False


@patch("saleor.webhook.observability.worker.get_buffer")
def test_buffer_put_multi_key_events(mock_get_buffer, buffer):
    mock_get_buffer.return_value = buffer
    events = {KEY: ["payload"], "buffer_b": ["payload"]}
    assert worker.buffer_put_multi_key_events(events) is True


@patch("saleor.webhook.observability.worker.get_buffer")
def test_buffer_put_multi_key_events_when_buffer_is_full(mock_get_buffer, buffer):
    mock_get_buffer.return_value = buffer
    for i in range(MAX_SIZE):
        buffer.put_event("payload")
    assert buffer.size() == MAX_SIZE
    events = {KEY: ["payload"], "buffer_b": ["payload"]}
    assert worker.buffer_put_multi_key_events(events) is False


@patch("saleor.webhook.observability.worker.buffer_put_multi_key_events")
def test_background_worker(mock_buffer_put_multi_key_events, init):
    buffer_name, payload = "buffer_a", "payload-{}"
    for i in range(BATCH_SIZE):
        worker.put_event(buffer_name, partial(payload.format, i))
    worker.shutdown_worker()
    mock_buffer_put_multi_key_events.assert_called_once_with(
        {buffer_name: [payload.format(i) for i in range(BATCH_SIZE)]}
    )


@patch("saleor.webhook.observability.worker.buffer_put_multi_key_events")
def test_background_worker_queue_no_timeout(
    mock_buffer_put_multi_key_events, init_no_timeout
):
    buffer_name, payload = "buffer_a", "payload-{}"
    worker.put_event(buffer_name, partial(payload.format, 0))
    worker.shutdown_worker()
    mock_buffer_put_multi_key_events.assert_called_once_with(
        {buffer_name: [payload.format(0)]}
    )


@patch("saleor.webhook.observability.worker.buffer_put_multi_key_events")
def test_background_worker_put_multi_buffer(mock_buffer_put_multi_key_events, init):
    buffer_a, buffer_b = "buffer_a", "buffer_b"
    payload = "payload-{}"
    for i in range(BATCH_SIZE // 2):
        worker.put_event(buffer_a, partial(payload.format, i))
        worker.put_event(buffer_b, partial(payload.format, i))
    worker.shutdown_worker()
    mock_buffer_put_multi_key_events.assert_called_once_with(
        {
            buffer_a: [payload.format(i) for i in range(BATCH_SIZE // 2)],
            buffer_b: [payload.format(i) for i in range(BATCH_SIZE // 2)],
        }
    )


@patch("saleor.webhook.observability.worker.buffer_put_multi_key_events")
def test_background_worker_queue_full(mock_buffer_put_multi_key_events, init):
    buffer_name, payload = "buffer_a", "payload-{}"
    for i in range(BATCH_SIZE):
        worker.put_event(buffer_name, partial(payload.format, i))
    assert worker.put_event(buffer_name, partial(payload.format, BATCH_SIZE)) is False
    worker.shutdown_worker()
    mock_buffer_put_multi_key_events.assert_called_once()


@patch("saleor.webhook.observability.worker.buffer_put_multi_key_events")
def test_background_worker_with_generate_payload_exception(
    mock_buffer_put_multi_key_events, init
):
    buffer_name, payload = "buffer_a", "payload-{}"
    worker.put_event(buffer_name, lambda: 1 / 0)
    for i in range(BATCH_SIZE - 1):
        worker.put_event(buffer_name, partial(payload.format, i))
    worker.shutdown_worker()
    mock_buffer_put_multi_key_events.assert_called_once_with(
        {buffer_name: [payload.format(i) for i in range(BATCH_SIZE - 1)]}
    )


@patch("saleor.webhook.observability.worker.buffer_put_multi_key_events")
def test_background_worker_failed_flush(mock_buffer_put_multi_key_events, init):
    buffer_name, payload = "buffer_a", "payload-{}"
    for i in range(BATCH_SIZE - 1):
        worker.put_event(buffer_name, partial(payload.format, i))
    worker.shutdown_worker(0.0)
    mock_buffer_put_multi_key_events.assert_not_called()
