from unittest.mock import MagicMock

import pytest
from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.models import WebhookEvent
from saleor.webhook.transport.synchronous.circuit_breaker.breaker_board import ENABLED_WEBHOOK_EVENT_TYPES, BreakerBoard
from saleor.webhook.transport.utils import WebhookResponse


# TODO - use (create) simpler fixter than `payment_app` fixture
def test_breaker_board(payment_app):
    assert WebhookEventSyncType.PAYMENT_LIST_GATEWAYS not in ENABLED_WEBHOOK_EVENT_TYPES

    mocked_func = MagicMock()
    mocked_func.return_value = WebhookResponse(content="bar", status=200), "bar"
    wrapped_mocked_func = BreakerBoard(mocked_func)
    event = WebhookEvent.objects.get(event_type=WebhookEventSyncType.PAYMENT_LIST_GATEWAYS)

    wrapped_mocked_func(event)

    mocked_func.assert_called_once()


def test_breaker_board_func_not_set(payment_app):
    wrapped_mocked_func = BreakerBoard()
    event = WebhookEvent.objects.get(event_type=WebhookEventSyncType.PAYMENT_LIST_GATEWAYS)

    with pytest.raises(RuntimeError):
        wrapped_mocked_func(event)
