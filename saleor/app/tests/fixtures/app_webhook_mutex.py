import pytest

from ...models import AppWebhookMutex


@pytest.fixture
def app_webhook_mutex(app):
    return AppWebhookMutex.objects.create(app=app)
