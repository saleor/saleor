import json
from datetime import datetime
from unittest.mock import patch

import pytest
import pytz
from celery.exceptions import Retry
from django.core.cache import cache
from django.http import HttpResponse
from freezegun import freeze_time

from ..payload_schema import JsonTruncText
from ..payloads import CustomJsonEncoder
from ..utils import (
    ApiCall,
    WebhookData,
    active_webhooks_exists,
    active_webhooks_exists_clear_cache,
    get_observability_webhooks,
    report_api_call,
    report_gql_operation,
    task_next_retry_date,
)


@pytest.fixture
def clear_cache():
    yield
    cache.clear()


def test_get_observability_webhooks(clear_cache, observability_app):
    webhook = observability_app.webhooks.first()
    observability_webhooks = get_observability_webhooks()
    assert observability_webhooks == [
        WebhookData(
            id=webhook.id,
            saleor_domain="mirumee.com",
            target_url=webhook.target_url,
            secret_key=webhook.secret_key,
        )
    ]


@patch("saleor.webhook.observability.utils.get_webhooks_for_event")
def test_get_observability_webhooks_cache(
    mocked_get_webhooks_for_event, clear_cache, observability_app
):
    webhook = observability_app.webhooks.first()
    mocked_get_webhooks_for_event.return_value = [webhook]
    get_observability_webhooks(), get_observability_webhooks()

    mocked_get_webhooks_for_event.assert_called_once()


def test_observability_webhooks_active(clear_cache, observability_app):
    active_webhooks_exists_clear_cache()
    assert active_webhooks_exists() is True


def test_observability_webhooks_active_when_app_deactivated(
    clear_cache, observability_app
):
    active_webhooks_exists_clear_cache()
    observability_app.is_active = False
    observability_app.save()

    assert active_webhooks_exists() is False


@patch("saleor.webhook.observability.utils.get_observability_webhooks")
def test_observability_webhooks_active_cache(
    mock_get_observability_webhooks, clear_cache, observability_app
):
    active_webhooks_exists_clear_cache()
    mock_get_observability_webhooks.return_value = []
    active_webhooks_exists(), active_webhooks_exists()

    mock_get_observability_webhooks.assert_called_once()


def test_custom_json_encoder_dumps_json_trunc_text():
    input_data = {"body": JsonTruncText("content", truncated=True)}

    serialized_data = json.dumps(input_data, cls=CustomJsonEncoder)

    data = json.loads(serialized_data)
    assert data["body"]["text"] == "content"
    assert data["body"]["truncated"] is True


@pytest.mark.parametrize(
    "text,limit,expected_size,expected_text,expected_truncated",
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


@pytest.mark.parametrize(
    "retry, next_retry_date",
    [
        (Retry(), None),
        (Retry(when=60 * 10), datetime(1914, 6, 28, 11, tzinfo=pytz.utc)),
        (Retry(when=datetime(1914, 6, 28, 11)), datetime(1914, 6, 28, 11)),
    ],
)
@freeze_time("1914-06-28 10:50")
def test_task_next_retry_date(retry, next_retry_date):
    assert task_next_retry_date(retry) == next_retry_date


@pytest.fixture
def test_request(rf):
    return rf.post("/graphql", data={"request": "data"})


@pytest.fixture
def observability_enabled(settings):
    settings.OBSERVABILITY_ACTIVE = True
    settings.OBSERVABILITY_REPORT_ALL_API_CALLS = False
    yield


@pytest.fixture
def observability_disabled(settings):
    settings.OBSERVABILITY_ACTIVE = False
    settings.OBSERVABILITY_REPORT_ALL_API_CALLS = False
    yield


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


@pytest.fixture
def api_call(test_request):
    api_call = ApiCall(request=test_request)
    api_call.response = HttpResponse({"response": "data"})
    return api_call


@patch("saleor.webhook.observability.utils.put_to_buffer")
@patch("saleor.webhook.observability.utils.active_webhooks_exists")
def test_api_call_report(
    mock_active_webhooks_exists,
    mock_put_to_buffer,
    observability_enabled,
    app,
    api_call,
    test_request,
):
    mock_active_webhooks_exists.return_value = True
    test_request.app = app
    api_call.report(), api_call.report()

    mock_put_to_buffer.assert_called_once()


@patch("saleor.webhook.observability.utils.active_webhooks_exists")
def test_api_call_response_report_when_observability_not_active(
    mock_active_webhooks_exists, observability_disabled, api_call
):
    api_call.report()

    mock_active_webhooks_exists.assert_not_called()


@patch("saleor.webhook.observability.utils.active_webhooks_exists")
def test_api_call_response_report_when_request_not_from_app(
    mock_active_webhooks_exists, observability_enabled, api_call
):
    api_call.report()

    mock_active_webhooks_exists.assert_not_called()
