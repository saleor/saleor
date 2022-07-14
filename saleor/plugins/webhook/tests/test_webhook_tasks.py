import pytest

from ....app.models import App
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook, WebhookEvent
from ....webhook.utils import get_webhooks_for_event


@pytest.fixture
def webhooks_factory():
    def factory(apps, event_type):
        webhooks = [Webhook(name=f"Webhook {i}", app=app) for i, app in enumerate(apps)]
        Webhook.objects.bulk_create(webhooks)
        WebhookEvent.objects.bulk_create(
            WebhookEvent(event_type=event_type, webhook=webhook) for webhook in webhooks
        )

    return factory


def test_get_webhooks_for_event_webhook_ordering(webhooks_factory):
    # given
    apps = [App(name=f"App {i}", is_active=True) for i in range(3)]
    App.objects.bulk_create(apps)
    event_type = WebhookEventAsyncType.PRODUCT_CREATED
    webhooks_factory([apps[1], apps[1], apps[2], apps[0]], event_type)

    # when
    webhooks = list(get_webhooks_for_event(event_type))

    # then
    for prev_webhook, next_webhook in zip(webhooks, webhooks[1:]):
        assert prev_webhook.app_id <= next_webhook.app_id
        if prev_webhook.app_id == next_webhook.app_id:
            assert prev_webhook.pk < next_webhook.pk
