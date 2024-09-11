from unittest.mock import MagicMock

import pytest

from saleor.app.models import App
from saleor.core import EventDeliveryStatus
from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.models import Webhook, WebhookEvent
from saleor.webhook.transport.synchronous.circuit_breaker.breaker_board import (
    BreakerBoard,
)
from saleor.webhook.transport.synchronous.circuit_breaker.storage import InMemoryStorage
from saleor.webhook.transport.utils import WebhookResponse


@pytest.fixture
def app_with_webhook(db):
    app = App.objects.create(
        name="Webhook App", is_active=True, identifier="saleor.webhook.test.app"
    )

    webhook = Webhook.objects.create(
        name="webhook-1",
        app=app,
        target_url="https://webhook-1.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                               WebhookEventSyncType.PAYMENT_CAPTURE]
        ]
    )
    return app


@pytest.fixture
def success_response_function_mock():
    mocked_func = MagicMock()
    mocked_func.return_value = WebhookResponse(content="good", status=EventDeliveryStatus.SUCCESS), "good"
    return mocked_func


@pytest.fixture
def failed_response_function_mock():
    mocked_func = MagicMock()
    mocked_func.return_value = WebhookResponse(content="bad", status=EventDeliveryStatus.FAILED), "bad"
    return mocked_func

def test_breaker_board_failure(app_with_webhook, failed_response_function_mock):
    breaker_board = BreakerBoard(storage=InMemoryStorage(), failure_threshold=1)

    event = WebhookEvent.objects.get(event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT)
    assert WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT in breaker_board.webhook_event_types
    wrapped_function_mock = breaker_board(failed_response_function_mock)

    assert failed_response_function_mock.call_count == 0

    wrapped_function_mock(event)
    wrapped_function_mock(event)

    # Only one call was made due to failure threshold
    assert failed_response_function_mock.call_count == 1
    assert breaker_board.storage.last_open(app_with_webhook.id) != 0


def test_breaker_board_failure_ignored_webhook_event_type(app_with_webhook, failed_response_function_mock):
    breaker_board = BreakerBoard(storage=InMemoryStorage(), failure_threshold=1)

    event = WebhookEvent.objects.get(event_type=WebhookEventSyncType.PAYMENT_CAPTURE)
    assert WebhookEventSyncType.PAYMENT_CAPTURE not in breaker_board.webhook_event_types
    wrapped_function_mock = breaker_board(failed_response_function_mock)

    assert failed_response_function_mock.call_count == 0

    wrapped_function_mock(event)
    wrapped_function_mock(event)

    # Two calls were made despite failure threshold due to webhook event type
    assert failed_response_function_mock.call_count == 2
    assert breaker_board.storage.last_open(app_with_webhook.id) == 0


def test_breaker_board_success(app_with_webhook, success_response_function_mock):
    breaker_board = BreakerBoard(storage=InMemoryStorage(), failure_threshold=1)

    event = WebhookEvent.objects.get(event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT)
    assert WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT in breaker_board.webhook_event_types
    wrapped_function_mock = breaker_board(success_response_function_mock)

    assert success_response_function_mock.call_count == 0

    wrapped_function_mock(event)
    wrapped_function_mock(event)

    assert success_response_function_mock.call_count == 2
    assert breaker_board.storage.last_open(app_with_webhook.id) == 0
