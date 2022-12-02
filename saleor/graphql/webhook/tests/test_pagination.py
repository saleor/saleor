import pytest

from ....app.models import App
from ....webhook.models import Webhook


@pytest.fixture
def webhooks_for_pagination(db):
    apps = App.objects.bulk_create(
        [App(name="App1", is_active=True), App(name="App2", is_active=True)]
    )

    return Webhook.objects.bulk_create(
        [
            Webhook(
                name="Webhook1",
                app=apps[1],
                target_url="http://www.example.com/test4",
                is_active=False,
            ),
            Webhook(
                name="WebhookWebhook1",
                app=apps[0],
                target_url="http://www.example.com/test2",
            ),
            Webhook(
                name="WebhookWebhook2",
                app=apps[1],
                target_url="http://www.example.com/test1",
            ),
            Webhook(
                name="Webhook2",
                app=apps[1],
                target_url="http://www.example.com/test3",
                is_active=False,
            ),
            Webhook(
                name="Webhook3",
                app=apps[0],
                target_url="http://www.example.com/test",
            ),
        ]
    )
