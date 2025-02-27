import pytest
from django.core.exceptions import ImproperlyConfigured

from ....graphql.app.enums import CircuitBreakerState
from ....webhook.event_types import WebhookEventSyncType
from .utils import create_breaker_board


def test_breaker_board_failure(
    settings, breaker_storage, app_with_webhook, failed_response_function_mock
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(breaker_storage)
    app, webhook = app_with_webhook
    wrapped_function_mock = breaker_board(failed_response_function_mock)
    assert failed_response_function_mock.call_count == 0

    # when
    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )
    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )
    breaker_board.update_breaker_state(app)

    # then only one call was made due to failure threshold
    assert failed_response_function_mock.call_count == 1
    status, changed_at = breaker_board.storage.get_app_state(app.id)
    assert status == CircuitBreakerState.OPEN
    assert changed_at > 0


def test_breaker_board_failure_ignored_webhook_event_type(
    settings, breaker_storage, app_with_webhook, failed_response_function_mock
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(breaker_storage)
    app, webhook = app_with_webhook
    wrapped_function_mock = breaker_board(failed_response_function_mock)
    assert failed_response_function_mock.call_count == 0

    # when
    wrapped_function_mock(WebhookEventSyncType.PAYMENT_CAPTURE, "", webhook, False)
    wrapped_function_mock(WebhookEventSyncType.PAYMENT_CAPTURE, "", webhook, False)

    # then two calls were made despite failure threshold due to webhook event type
    assert failed_response_function_mock.call_count == 2
    status, changed_at = breaker_board.storage.get_app_state(app.id)
    assert status == CircuitBreakerState.CLOSED
    assert changed_at == 0


def test_breaker_board_success(
    settings, breaker_storage, app_with_webhook, success_response_function_mock
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(breaker_storage)
    app, webhook = app_with_webhook
    wrapped_function_mock = breaker_board(success_response_function_mock)
    assert success_response_function_mock.call_count == 0

    # when
    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )
    wrapped_function_mock(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, False
    )
    breaker_board.update_breaker_state(app)

    # then
    assert success_response_function_mock.call_count == 2
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
    failed_response_function_mock,
    success_response_function_mock,
):
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(
        breaker_storage,
        failure_threshold=threshold,
        failure_min_count=1,
    )
    # given
    app, webhook = app_with_webhook
    wrapped_function_mock_success = breaker_board(success_response_function_mock)
    wrapped_function_mock_failed = breaker_board(failed_response_function_mock)

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
    failed_response_function_mock,
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    breaker_board = create_breaker_board(
        breaker_storage, failure_threshold=3, failure_min_count=1
    )
    app, webhook = app_with_webhook
    wrapped_function_mock_failed = breaker_board(failed_response_function_mock)

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
