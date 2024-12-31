from unittest.mock import MagicMock

import pytest

from saleor.app.models import App
from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.models import Webhook, WebhookEvent


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
            for event_type in [
                WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                WebhookEventSyncType.PAYMENT_CAPTURE,
            ]
        ]
    )
    return app, webhook


@pytest.fixture
def success_response_function_mock():
    mocked_func = MagicMock()
    mocked_func.return_value = {"data": "some"}
    return mocked_func


@pytest.fixture
def failed_response_function_mock():
    mocked_func = MagicMock()
    mocked_func.return_value = None
    return mocked_func
