import pytest

from ...webhook.event_types import WebhookEventSyncType
from ...webhook.models import Webhook
from ..manager import get_plugins_manager


@pytest.fixture
def tax_app(app, permission_handle_taxes, webhook):
    app.permissions.add(permission_handle_taxes)
    return app


@pytest.fixture
def tax_checkout_webhook(tax_app):
    webhook = Webhook.objects.create(
        name="Tax checkout webhook",
        app=tax_app,
        target_url="https://www.example.com/tax-checkout",
    )
    webhook.events.create(event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES)
    return webhook


@pytest.fixture
def tax_order_webhook(tax_app):
    webhook = Webhook.objects.create(
        name="Tax order webhook",
        app=tax_app,
        target_url="https://www.example.com/tax-order",
    )
    webhook.events.create(event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES)
    return webhook


@pytest.fixture
def tax_app_with_webhooks(tax_app, tax_checkout_webhook, tax_order_webhook):
    return tax_app


@pytest.fixture
def webhook_plugin(settings):
    def factory():
        settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
        manager = get_plugins_manager(allow_replica=False)
        manager.get_all_plugins()
        return manager.global_plugins[0]

    return factory
