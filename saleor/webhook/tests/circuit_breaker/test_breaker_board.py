from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ImproperlyConfigured
from promise import Promise

from ....graphql.app.enums import CircuitBreakerState
from ....webhook.event_types import WebhookEventSyncType
from .utils import create_breaker_board


def test_breaker_board_failure_for_promise_wrapper(
    settings, breaker_storage, app_with_webhook
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(breaker_storage)
    app, webhook = app_with_webhook

    wrapped_mocked_promise_func = MagicMock(return_value=Promise.resolve(None))
    wrapped_function_mock = breaker_board.wrap_promise_func(wrapped_mocked_promise_func)

    # when
    wrapped_function_mock(
        event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        static_payload="",
        webhook=webhook,
        allow_replica=True,
    ).get()

    wrapped_function_mock(
        event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        static_payload="",
        webhook=webhook,
        allow_replica=True,
    ).get()
    breaker_board.update_breaker_state(app)

    # then only one call was made due to failure threshold
    assert wrapped_mocked_promise_func.call_count == 1
    status, changed_at = breaker_board.storage.get_app_state(app.id)
    assert status == CircuitBreakerState.OPEN
    assert changed_at > 0


def test_breaker_board_failure_ignored_webhook_event_type_for_promise_func_wrapper(
    settings,
    breaker_storage,
    app_with_webhook,
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(breaker_storage)
    app, webhook = app_with_webhook

    wrapped_mocked_promise_func = MagicMock(return_value=Promise.resolve(None))
    wrapped_function_mock = breaker_board.wrap_promise_func(wrapped_mocked_promise_func)

    # when
    wrapped_function_mock(
        event_type=WebhookEventSyncType.PAYMENT_CAPTURE,
        static_payload="",
        webhook=webhook,
        allow_replica=True,
    )
    wrapped_function_mock(
        event_type=WebhookEventSyncType.PAYMENT_CAPTURE,
        static_payload="",
        webhook=webhook,
        allow_replica=True,
    )

    # then two calls were made despite failure threshold due to webhook event type
    assert wrapped_mocked_promise_func.call_count == 2
    status, changed_at = breaker_board.storage.get_app_state(app.id)
    assert status == CircuitBreakerState.CLOSED
    assert changed_at == 0


def test_breaker_board_success_for_promise_func_wrapper(
    settings, breaker_storage, app_with_webhook
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(breaker_storage)
    app, webhook = app_with_webhook

    wrapped_mocked_promise_func = MagicMock(return_value=Promise.resolve(None))
    wrapped_function_mock = breaker_board.wrap_promise_func(wrapped_mocked_promise_func)

    # when
    wrapped_function_mock(
        event_type=WebhookEventSyncType.PAYMENT_CAPTURE,
        static_payload="",
        webhook=webhook,
        allow_replica=True,
    )
    wrapped_function_mock(
        event_type=WebhookEventSyncType.PAYMENT_CAPTURE,
        static_payload="",
        webhook=webhook,
        allow_replica=True,
    )
    breaker_board.update_breaker_state(app)

    # then
    assert wrapped_mocked_promise_func.call_count == 2
    status, changed_at = breaker_board.storage.get_app_state(app.id)
    assert status == CircuitBreakerState.CLOSED
    assert changed_at == 0


@pytest.mark.parametrize(
    ("success_attempts", "failed_attempts", "threshold", "breaker_status"),
    [
        (5, 5, 50, CircuitBreakerState.OPEN),
        (5, 5, 51, CircuitBreakerState.CLOSED),
        (4, 6, 50, CircuitBreakerState.OPEN),
        (8, 2, 20, CircuitBreakerState.OPEN),
        (8, 2, 21, CircuitBreakerState.CLOSED),
    ],
)
def test_breaker_board_threshold(
    success_attempts,
    failed_attempts,
    threshold,
    breaker_status,
    settings,
    breaker_storage,
    app_with_webhook,
):
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(
        breaker_storage,
        failure_threshold=threshold,
        failure_min_count=1,
    )
    # given
    app, webhook = app_with_webhook
    wrapped_failed_mocked_promise_func = MagicMock(return_value=Promise.resolve(None))
    wrapped_success_mocked_promise_func = MagicMock(
        return_value=Promise.resolve({"data": "some"})
    )
    wrapped_function_mock_success = breaker_board.wrap_promise_func(
        wrapped_success_mocked_promise_func
    )
    wrapped_function_mock_failed = breaker_board.wrap_promise_func(
        wrapped_failed_mocked_promise_func
    )

    # when
    for _ in range(success_attempts):
        wrapped_function_mock_success(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
        )
    for _ in range(failed_attempts):
        wrapped_function_mock_failed(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
        )
    breaker_board.update_breaker_state(app)

    # then
    status, _ = breaker_board.storage.get_app_state(app.id)
    assert status == breaker_status


def test_breaker_board_clear_state_for_app(
    settings,
    breaker_storage,
    app_with_webhook,
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(
        breaker_storage, failure_threshold=3, failure_min_count=1
    )
    app, webhook = app_with_webhook

    wrapped_failed_mocked_promise_func = MagicMock(return_value=Promise.resolve(None))
    wrapped_function_mock_failed = breaker_board.wrap_promise_func(
        wrapped_failed_mocked_promise_func
    )

    # when
    for _ in range(3):
        wrapped_function_mock_failed(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
        )
    breaker_board.update_breaker_state(app)
    status, changed_at = breaker_board.storage.get_app_state(app.id)
    assert status == CircuitBreakerState.OPEN
    assert changed_at > 0
    error = breaker_board.storage.clear_state_for_app(app.id)

    # then
    assert not error
    status, changed_at = breaker_board.storage.get_app_state(app.id)
    assert status == CircuitBreakerState.CLOSED
    assert changed_at == 0


def test_breaker_board_configuration_invalid_events(settings, breaker_storage):
    # given
    event_name = "invalid"
    settings.BREAKER_BOARD_SYNC_EVENTS = [event_name]

    # when
    with pytest.raises(ImproperlyConfigured) as e:
        create_breaker_board(breaker_storage)

    # then
    assert (
        e.value.args[0] == f'Event "{event_name}" is not supported by circuit breaker.'
    )


def test_breaker_board_configuration_empty_event(settings, breaker_storage):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = []

    # when
    with pytest.raises(ImproperlyConfigured) as e:
        create_breaker_board(breaker_storage)

    # then
    assert e.value.args[0] == "BREAKER_BOARD_SYNC_EVENTS cannot be empty."


def test_breaker_board_configuration_mixed_events(settings, breaker_storage):
    # given
    bad_event_name = "bad_event"
    settings.BREAKER_BOARD_SYNC_EVENTS = [
        "checkout_calculate_taxes",
        "shipping_list_methods_for_checkout",
        bad_event_name,
    ]

    # when
    with pytest.raises(ImproperlyConfigured) as e:
        create_breaker_board(breaker_storage)

    # then
    assert (
        e.value.args[0]
        == f'Event "{bad_event_name}" is not supported by circuit breaker.'
    )


def test_breaker_board_configuration_unexpected_dry_run_event(
    settings, breaker_storage
):
    # given
    event_name = "shipping_list_methods_for_checkout"
    settings.BREAKER_BOARD_SYNC_EVENTS = ["checkout_calculate_taxes"]
    settings.BREAKER_BOARD_DRY_RUN_SYNC_EVENTS = [event_name]

    # when
    with pytest.raises(ImproperlyConfigured) as e:
        create_breaker_board(breaker_storage)

    # then
    assert (
        e.value.args[0]
        == f'Dry-run event "{event_name}" is not monitored by circuit breaker.'
    )
