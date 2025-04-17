import pytest

from ...models import AppWebhookMutex


@pytest.fixture
def app_webhook_mutex(app):
    return AppWebhookMutex.objects.create(app=app)


@pytest.fixture
def removed_app_webhook_mutex(removed_app):
    return AppWebhookMutex.objects.create(app=removed_app)


@pytest.fixture
def webhook_app_webhook_mutex(webhook_app):
    return AppWebhookMutex.objects.create(app=webhook_app)
