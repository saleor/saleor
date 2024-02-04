import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from django.http import HttpResponse
from freezegun import freeze_time

from ..exceptions import ApiCallTruncationError, EventDeliveryAttemptTruncationError
from ..payload_schema import JsonTruncText
from ..payloads import CustomJsonEncoder
from ..utils import (
    ApiCall,
    get_webhooks,
    get_webhooks_clear_mem_cache,
    pop_events_with_remaining_size,
    put_event,
    report_api_call,
    report_event_delivery_attempt,
    report_gql_operation,
    task_next_retry_date,
)
from .conftest import BATCH_SIZE


@pytest.fixture
def api_call(test_request):
    api_call = ApiCall(request=test_request)
    api_call.response = HttpResponse({"response": "data"})
    return api_call


@pytest.fixture
def patch_get_buffer(buffer):
    with patch(
        "saleor.webhook.observability.utils.get_buffer", return_value=buffer
    ) as get_buffer:
        yield get_buffer


@pytest.fixture
def patch_get_webhooks(observability_webhook_data):
    with patch(
        "saleor.webhook.observability.utils.get_webhooks",
        return_value=observability_webhook_data,
    ) as get_webhooks:
        yield get_webhooks


@pytest.fixture
def test_request(rf):
    return rf.post("/graphql", data={"request": "data"})


@pytest.fixture
def _observability_enabled(settings):
    settings.OBSERVABILITY_ACTIVE = True
    settings.OBSERVABILITY_REPORT_ALL_API_CALLS = False


@pytest.fixture
def _observability_disabled(settings):
    settings.OBSERVABILITY_ACTIVE = False
    settings.OBSERVABILITY_REPORT_ALL_API_CALLS = False


@patch("saleor.webhook.observability.utils.cache.get")
@patch("saleor.webhook.observability.utils.get_webhooks_for_event")
def test_get_webhooks(
    mocked_get_webhooks_for_event,
    mock_cache_get,
    _clear_cache,
    observability_webhook,
    observability_webhook_data,
):
    get_webhooks_clear_mem_cache()
    mocked_get_webhooks_for_event.return_value = [observability_webhook]
    mock_cache_get.side_effect = [None, [observability_webhook_data]]

    assert get_webhooks() == [observability_webhook_data]
    get_webhooks_clear_mem_cache()
    assert get_webhooks() == [observability_webhook_data]
    assert get_webhooks() == [observability_webhook_data]
    assert get_webhooks() == [observability_webhook_data]
    assert mock_cache_get.call_count == 2
    mocked_get_webhooks_for_event.assert_called_once()


def test_custom_json_encoder_dumps_json_trunc_text():
    input_data = {"body": JsonTruncText("content", truncated=True)}

    serialized_data = json.dumps(input_data, cls=CustomJsonEncoder)

    data = json.loads(serialized_data)
    assert data["body"]["text"] == "content"
    assert data["body"]["truncated"] is True


@pytest.mark.parametrize(
    ("text", "limit", "expected_size", "expected_text", "expected_truncated"),
    [
        ("abcde", 5, 5, "abcde", False),
        ("abó", 3, 2, "ab", True),
        ("abó", 8, 8, "abó", False),
        ("abó", 12, 8, "abó", False),
        ("a\nc𐀁d", 17, 17, "a\nc𐀁d", False),
        ("a\nc𐀁d", 10, 4, "a\nc", True),
        ("a\nc𐀁d", 16, 16, "a\nc𐀁", True),
        ("abcd", 0, 0, "", True),
    ],
)
def test_json_truncate_text_to_byte_limit(
    text, limit, expected_size, expected_text, expected_truncated
):
    truncated = JsonTruncText.truncate(text, limit)
    assert truncated.text == expected_text
    assert truncated.byte_size == expected_size
    assert truncated.truncated == expected_truncated
    assert len(json.dumps(truncated.text)) == expected_size + len('""')


def test_json_truncate_text_comparison():
    truncated_a = JsonTruncText("content", truncated=True)
    truncated_b = JsonTruncText("content", truncated=True)
    assert truncated_a != "content"
    assert truncated_a == truncated_b


@pytest.mark.parametrize(
    ("retry", "next_retry_date"),
    [
        (Retry(), None),
        (Retry(when=60 * 10), datetime(1914, 6, 28, 11, tzinfo=timezone.utc)),
        (Retry(when=datetime(1914, 6, 28, 11)), datetime(1914, 6, 28, 11)),
    ],
)
@freeze_time("1914-06-28 10:50")
def test_task_next_retry_date(retry, next_retry_date):
    assert task_next_retry_date(retry) == next_retry_date


@patch("saleor.webhook.observability.utils.ApiCall.report")
def test_report_api_call_scope(mocked_api_call_report, test_request):
    with report_api_call(test_request) as level_1:
        with report_api_call(test_request) as level_2:
            with report_api_call(test_request) as level_3:
                assert level_1 == level_2
                assert level_1 == level_3
                assert level_2 == level_3
                level_3.report()
    assert mocked_api_call_report.call_count == 2
    with report_api_call(test_request) as diff_scope:
        assert diff_scope != level_1


def test_report_gql_operation_scope(test_request):
    with report_api_call(test_request) as api_call:
        assert len(api_call.gql_operations) == 0
        with report_gql_operation() as operation_a:
            with report_gql_operation() as operation_a_l2:
                assert operation_a == operation_a_l2
        with report_gql_operation() as operation_b:
            pass
        assert len(api_call.gql_operations) == 2
        assert api_call.gql_operations == [operation_a, operation_b]


@patch("saleor.webhook.observability.utils.put_event")
def test_api_call_report(
    mock_put_event,
    _observability_enabled,
    patch_get_webhooks,
    app,
    api_call,
    test_request,
):
    test_request.app = app
    api_call.report()
    api_call.report()

    mock_put_event.assert_called_once()


@patch("saleor.webhook.observability.utils.put_event")
def test_api_call_response_report_when_observability_not_active(
    mock_put_event,
    _observability_disabled,
    patch_get_webhooks,
    api_call,
):
    api_call.report()

    patch_get_webhooks.assert_not_called()
    mock_put_event.assert_not_called()


@patch("saleor.webhook.observability.utils.put_event")
def test_api_call_response_report_when_request_not_from_app(
    mock_put_event,
    _observability_enabled,
    patch_get_webhooks,
    api_call,
):
    api_call.report()

    patch_get_webhooks.assert_not_called()
    mock_put_event.assert_not_called()


@patch("saleor.webhook.observability.utils.put_event")
def test_api_call_response_report_when_no_gql_response(
    mock_put_event,
    _observability_enabled,
    patch_get_webhooks,
    api_call,
):
    api_call.response = None
    api_call.report()

    patch_get_webhooks.assert_not_called()
    mock_put_event.assert_not_called()


@patch("saleor.webhook.observability.utils.put_event")
def test_report_event_delivery_attempt(
    mock_put_event,
    _observability_enabled,
    patch_get_webhooks,
    event_attempt,
):
    report_event_delivery_attempt(event_attempt)
    mock_put_event.assert_called_once()


@patch("saleor.webhook.observability.utils.put_event")
def test_report_event_delivery_attempt_not_active(
    mock_put_event,
    _observability_disabled,
    patch_get_webhooks,
    event_attempt,
):
    report_event_delivery_attempt(event_attempt)
    mock_put_event.assert_not_called()


def test_put_event(patch_get_buffer, buffer, event_data):
    put_event(lambda: event_data)
    assert buffer.size() == 1


@pytest.mark.parametrize(
    "error",
    [
        Exception("Unknown error"),
        ApiCallTruncationError("operation_name", 100, 102, extra_kwarg="extra"),
        EventDeliveryAttemptTruncationError(
            "operation_name", 100, 102, extra_kwarg="extra"
        ),
    ],
)
def test_put_event_catch_exceptions(patch_get_buffer, buffer, error):
    def error_source():
        raise error

    put_event(error_source)
    assert buffer.size() == 0


def test_pop_events_with_remaining_size(patch_get_buffer, buffer):
    payloads_count = BATCH_SIZE + (BATCH_SIZE // 2)
    payloads = [f"event-data-{i}".encode() for i in range(payloads_count)]
    buffer.put_events(payloads)

    events, remaining_batch_count = pop_events_with_remaining_size()

    assert events == [f"event-data-{i}".encode() for i in range(BATCH_SIZE)]
    assert remaining_batch_count == 1


def test_pop_events_with_remaining_size_catch_exceptions(
    redis_server, buffer, patch_get_buffer
):
    buffer.put_events([f"event-data-{i}".encode() for i in range(BATCH_SIZE)])
    redis_server.connected = False
    assert pop_events_with_remaining_size() == ([], 0)
