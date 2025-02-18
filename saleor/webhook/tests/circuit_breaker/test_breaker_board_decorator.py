from unittest.mock import Mock, patch

from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.transport.synchronous import transport

from ....graphql.app.types import CircuitBreakerState
from .utils import create_breaker_board

# The intention is to test whether BreakerBoard decorator is compatible with
# `trigger_webhook_sync` function, the actual logic of sending a webhook request is
# mocked.


def test_breaker_board(
    settings,
    breaker_storage,
    app_with_webhook,
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    expected_data = {"some": "data"}
    _, webhook = app_with_webhook
    breaker_board = create_breaker_board(breaker_storage)
    transport.trigger_webhook_sync = breaker_board(transport.trigger_webhook_sync)
    assert hasattr(transport.trigger_webhook_sync, "__wrapped__") is True

    # when
    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=expected_data),
    ):
        response_data = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    # then
    assert response_data == expected_data


def test_breaker_board_trip(settings, breaker_storage, app_with_webhook, caplog):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    _, webhook = app_with_webhook
    cooldown = 30
    breaker_board = create_breaker_board(breaker_storage, cooldown_seconds=cooldown)
    transport.trigger_webhook_sync = breaker_board(transport.trigger_webhook_sync)
    breaker_board.register_error(app_with_webhook[0].id, 100)

    # when
    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=None),
    ):
        response_data = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    # then
    assert response_data is None
    assert caplog.messages == [
        f"[App ID: {app_with_webhook[0].id!r}] Circuit breaker tripped, cooldown is {cooldown} [seconds]."
    ]


def test_breaker_board_enter_half_open(
    settings, breaker_storage, app_with_webhook, caplog
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    app, webhook = app_with_webhook
    breaker_board = create_breaker_board(breaker_storage)
    transport.trigger_webhook_sync = breaker_board(transport.trigger_webhook_sync)
    breaker_board.storage.update_open(app.id, 0, CircuitBreakerState.OPEN)

    # when
    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=None),
    ):
        response_data = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    # then
    assert response_data is None
    assert caplog.messages == [
        f"[App ID: {app_with_webhook[0].id!r}] Circuit breaker state changed to half_open."
    ]


def test_breaker_board_closes_on_half_open(
    settings, breaker_storage, app_with_webhook, caplog
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    app, webhook = app_with_webhook
    breaker_board = create_breaker_board(breaker_storage, success_count_recovery=1)
    transport.trigger_webhook_sync = breaker_board(transport.trigger_webhook_sync)
    breaker_board.storage.update_open(app.id, 0, CircuitBreakerState.HALF_OPEN)

    # when
    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=None),
    ):
        response_data = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    # then
    assert response_data is None
    assert caplog.messages == [
        f"[App ID: {app_with_webhook[0].id!r}] Circuit breaker fully recovered."
    ]


def test_breaker_board_closes_stays_half_open_below_threshold(
    settings, breaker_storage, app_with_webhook, caplog
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    app, webhook = app_with_webhook
    breaker_board = create_breaker_board(breaker_storage, success_count_recovery=2)
    transport.trigger_webhook_sync = breaker_board(transport.trigger_webhook_sync)
    breaker_board.storage.update_open(app.id, 0, CircuitBreakerState.HALF_OPEN)

    # when
    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=None),
    ):
        response_data = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    # then
    assert response_data is None
    assert caplog.messages == []


def test_breaker_board_reopens_on_half_open(
    settings, breaker_storage, app_with_webhook, caplog
):
    # given
    settings.BREAKER_BOARD_SYNC_EVENTS = ["shipping_list_methods_for_checkout"]
    app, webhook = app_with_webhook
    cooldown = 30
    breaker_board = create_breaker_board(
        breaker_storage, cooldown_seconds=cooldown, failure_min_count_recovery=1
    )
    transport.trigger_webhook_sync = breaker_board(transport.trigger_webhook_sync)
    breaker_board.register_error(app.id, 100)
    breaker_board.storage.update_open(app.id, 0, CircuitBreakerState.HALF_OPEN)

    # when
    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=None),
    ):
        response_data = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    # then
    assert response_data is None
    assert caplog.messages == [
        f"[App ID: {app_with_webhook[0].id!r}] Circuit breaker tripped, cooldown is {cooldown} [seconds]."
    ]
