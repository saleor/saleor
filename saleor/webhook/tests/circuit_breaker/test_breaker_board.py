import pytest
from django.core.exceptions import ImproperlyConfigured

from saleor.webhook.circuit_breaker.breaker_board import BreakerBoard
from saleor.webhook.circuit_breaker.storage import InMemoryStorage
from saleor.webhook.event_types import WebhookEventSyncType


def test_breaker_board_failure(
    settings, app_with_webhook, failed_response_function_mock
):
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=1,
        failure_min_count=0,
        cooldown_seconds=10,
        ttl_seconds=10,
    )
    app, webhook = app_with_webhook

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
    settings, app_with_webhook, failed_response_function_mock
):
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=1,
        failure_min_count=0,
        cooldown_seconds=10,
        ttl_seconds=10,
    )
    app, webhook = app_with_webhook

    wrapped_function_mock = breaker_board(failed_response_function_mock)

    assert failed_response_function_mock.call_count == 0

    wrapped_function_mock(WebhookEventSyncType.PAYMENT_CAPTURE, "", webhook, False)
    wrapped_function_mock(WebhookEventSyncType.PAYMENT_CAPTURE, "", webhook, False)

    # Two calls were made despite failure threshold due to webhook event type
    assert failed_response_function_mock.call_count == 2
    assert breaker_board.storage.last_open(app.id) == 0


def test_breaker_board_success(
    settings, app_with_webhook, success_response_function_mock
):
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=1,
        failure_min_count=0,
        cooldown_seconds=10,
        ttl_seconds=10,
    )
    app, webhook = app_with_webhook

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


@pytest.mark.parametrize(
    ("success_attempts", "failed_attempts", "threshold", "tripped"),
    [
        (5, 5, 50, True),
        (5, 5, 51, False),
        (4, 6, 50, True),
        (8, 2, 20, True),
        (8, 2, 21, False),
    ],
)
def test_breaker_board_threshold(
    success_attempts,
    failed_attempts,
    threshold,
    tripped,
    settings,
    app_with_webhook,
    failed_response_function_mock,
    success_response_function_mock,
):
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=threshold,
        failure_min_count=10,
        cooldown_seconds=10,
        ttl_seconds=10,
    )
    app, webhook = app_with_webhook

    wrapped_function_mock_success = breaker_board(success_response_function_mock)
    wrapped_function_mock_failed = breaker_board(failed_response_function_mock)

    for _ in range(success_attempts):
        wrapped_function_mock_success(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
        )

    for _ in range(failed_attempts):
        wrapped_function_mock_failed(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
        )

    assert bool(breaker_board.storage.last_open(app.id)) == tripped


def test_breaker_board_clear_state_for_app(
    settings,
    app_with_webhook,
    failed_response_function_mock,
):
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = BreakerBoard(
        storage=InMemoryStorage(),
        failure_threshold=3,
        failure_min_count=1,
        cooldown_seconds=10,
        ttl_seconds=10,
    )
    app, webhook = app_with_webhook
    wrapped_function_mock_failed = breaker_board(failed_response_function_mock)

    for _ in range(3):
        wrapped_function_mock_failed(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
        )

    assert bool(breaker_board.storage.last_open(app.id))

    error = breaker_board.storage.clear_state_for_app(app.id)
    assert not error
    assert not bool(breaker_board.storage.last_open(app.id))


def test_breaker_board_configuration_invalid_events(settings):
    event_name = "invalid"
    settings.BREAKER_BOARD_SYNC_EVENTS = [event_name]
    with pytest.raises(ImproperlyConfigured) as e:
        BreakerBoard(
            storage=InMemoryStorage(),
            failure_threshold=3,
            failure_min_count=1,
            cooldown_seconds=10,
            ttl_seconds=10,
        )
    assert (
        e.value.args[0] == f'Event "{event_name}" is not supported by circuit breaker.'
    )


def test_breaker_board_configuration_empty_event(settings):
    event_name = ""
    settings.BREAKER_BOARD_SYNC_EVENTS = [event_name]
    with pytest.raises(ImproperlyConfigured) as e:
        BreakerBoard(
            storage=InMemoryStorage(),
            failure_threshold=3,
            failure_min_count=1,
            cooldown_seconds=10,
            ttl_seconds=10,
        )
    assert e.value.args[0] == "BREAKER_BOARD_SYNC_EVENTS cannot be empty."


def test_breaker_board_configuration_miexed_events(settings):
    bad_event_name = "bad_event"
    settings.BREAKER_BOARD_SYNC_EVENTS = [
        "checkout_calculate_taxes",
        "shipping_list_methods_for_checkout",
        bad_event_name,
    ]
    with pytest.raises(ImproperlyConfigured) as e:
        BreakerBoard(
            storage=InMemoryStorage(),
            failure_threshold=3,
            failure_min_count=1,
            cooldown_seconds=10,
            ttl_seconds=10,
        )
    assert (
        e.value.args[0]
        == f'Event "{bad_event_name}" is not supported by circuit breaker.'
    )
