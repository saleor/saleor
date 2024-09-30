from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.transport.synchronous.circuit_breaker.breaker_board import (
    BreakerBoard,
)
from saleor.webhook.transport.synchronous.circuit_breaker.storage import InMemoryStorage


def test_breaker_board_failure(app_with_webhook, failed_response_function_mock):
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=1,
        failure_min_count=0,
        cooldown_seconds=10,
        ttl=10,
    )
    app, webhook = app_with_webhook

    assert (
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
        in breaker_board.webhook_event_types
    )
    wrapped_function_mock = breaker_board(failed_response_function_mock)

    assert failed_response_function_mock.call_count == 0

    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )
    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )

    # Only one call was made due to failure threshold
    assert failed_response_function_mock.call_count == 1
    assert breaker_board.storage.last_open(app.id) != 0


def test_breaker_board_failure_ignored_webhook_event_type(
    app_with_webhook, failed_response_function_mock
):
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=1,
        failure_min_count=0,
        cooldown_seconds=10,
        ttl=10,
    )
    app, webhook = app_with_webhook

    assert WebhookEventSyncType.PAYMENT_CAPTURE not in breaker_board.webhook_event_types
    wrapped_function_mock = breaker_board(failed_response_function_mock)

    assert failed_response_function_mock.call_count == 0

    wrapped_function_mock(WebhookEventSyncType.PAYMENT_CAPTURE, "", webhook, False)
    wrapped_function_mock(WebhookEventSyncType.PAYMENT_CAPTURE, "", webhook, False)

    # Two calls were made despite failure threshold due to webhook event type
    assert failed_response_function_mock.call_count == 2
    assert breaker_board.storage.last_open(app.id) == 0


def test_breaker_board_success(app_with_webhook, success_response_function_mock):
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=1,
        failure_min_count=0,
        cooldown_seconds=10,
        ttl=10,
    )
    app, webhook = app_with_webhook

    assert (
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
        in breaker_board.webhook_event_types
    )
    wrapped_function_mock = breaker_board(success_response_function_mock)

    assert success_response_function_mock.call_count == 0

    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )
    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )

    assert success_response_function_mock.call_count == 2
    assert breaker_board.storage.last_open(app.id) == 0
