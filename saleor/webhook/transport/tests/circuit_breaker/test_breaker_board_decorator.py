from importlib import reload
from unittest.mock import Mock, patch

import pytest

from saleor.webhook.event_types import WebhookEventSyncType

# The intention is to test whether BreakerBoard decorator is compatible with
# `trigger_webhook_sync` function, the actual logic of sending a webhook request is
# mocked.


@pytest.mark.parametrize(
    ("enable_breaker_board", "storage_class_string"),
    [
        (
            True,
            "saleor.webhook.transport.synchronous.circuit_breaker.storage.InMemoryStorage",
        ),
        (False, None),
    ],
)
def test_breaker_board(
    enable_breaker_board,
    storage_class_string,
    settings,
    app_with_webhook,
):
    expected_data = {"some": "data"}

    settings.ENABLE_BREAKER_BOARD = enable_breaker_board
    settings.BREAKER_BOARD_STORAGE_CLASS_STRING = storage_class_string
    _, webhook = app_with_webhook

    # Import alone is not sufficient, once module is imported the subsequent tests will
    # use the cached module.
    from saleor.webhook.transport.synchronous import transport

    reload(transport)

    assert (
        hasattr(transport.trigger_webhook_sync, "__wrapped__") is enable_breaker_board
    )

    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=expected_data),
    ):
        response_data = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    assert response_data == expected_data


def test_breaker_board_open(settings, app_with_webhook):
    settings.ENABLE_BREAKER_BOARD = True
    settings.BREAKER_BOARD_STORAGE_CLASS_STRING = (
        "saleor.webhook.transport.synchronous.circuit_breaker.storage.InMemoryStorage"
    )
    settings.BREAKER_BOARD_FAILURE_THRESHOLD = 1
    _, webhook = app_with_webhook

    # Import alone is not sufficient, once module is imported the subsequent tests will
    # use the cached module.
    from saleor.webhook.transport.synchronous import transport

    reload(transport)

    assert hasattr(transport.trigger_webhook_sync, "__wrapped__") is True

    # The return value is None which is considered an error.
    # The second webhook call encounters an open circuit breaker.
    with patch(
        "saleor.webhook.transport.synchronous.transport.send_webhook_request_sync",
        new=Mock(return_value=None),
    ):
        response_data_1 = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )
        response_data_2 = transport.trigger_webhook_sync(
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, "", webhook, True
        )

    assert response_data_1 is None
    assert response_data_2 is None
