import json
from datetime import datetime
from unittest.mock import patch

import pytest
import pytz
from celery.exceptions import Retry
from django.core.cache import cache
from freezegun import freeze_time

from ..payload_schema import JsonTruncText
from ..payloads import CustomJsonEncoder
from ..utils import (
    WebhookData,
    _webhooks_active_cache,
    get_observability_webhooks,
    observability_webhooks_active,
    task_next_retry_date,
)


@pytest.fixture
def reset_cache():
    yield
    cache.clear()


def test_get_observability_webhooks(reset_cache, observability_app):
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
    mocked_get_webhooks_for_event, reset_cache, observability_app
):
    webhook = observability_app.webhooks.first()
    mocked_get_webhooks_for_event.return_value = [webhook]
    get_observability_webhooks(), get_observability_webhooks()

    mocked_get_webhooks_for_event.assert_called_once()


def test_observability_webhooks_active(reset_cache, observability_app):
    _webhooks_active_cache.clear()
    assert observability_webhooks_active() is True


def test_observability_webhooks_active_when_app_deactivated(
    reset_cache, observability_app
):
    _webhooks_active_cache.clear()
    observability_app.is_active = False
    observability_app.save()

    assert observability_webhooks_active() is False


@patch("saleor.webhook.observability.utils.get_observability_webhooks")
def test_observability_webhooks_active_cache(
    mocked_get_observability_webhooks, reset_cache, observability_app
):
    _webhooks_active_cache.clear()
    mocked_get_observability_webhooks.return_value = []
    observability_webhooks_active(), observability_webhooks_active()

    mocked_get_observability_webhooks.assert_called_once()


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
