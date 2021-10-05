import json
from collections import namedtuple
from unittest import mock

import pytest
from django.conf import settings

from ....app.models import App
from ....payment import PaymentError, TransactionKind
from ....payment.utils import create_payment_information
from ....webhook.event_types import WebhookEventType
from ....webhook.models import Webhook, WebhookEvent
from ...manager import get_plugins_manager
from ..tasks import (
    send_webhook_request,
    send_webhook_request_sync,
    signature_for_payload,
    trigger_webhook_sync,
    trigger_webhooks_for_event
)
from ..utils import (
    parse_list_payment_gateways_response,
    parse_payment_action_response,
    to_payment_app_id,
)

@pytest.fixture
def webhook_plugin(settings):
    def factory():
        settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
        manager = get_plugins_manager()
        return manager.global_plugins[0]

    return factory

@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request):
    data = {"key": "value"}
    trigger_webhooks_for_event(WebhookEventType.ORDER_FILTER_SHIPPING_METHODS, data)
    mock_request.assert_called_once()