import pytest

from saleor.app.models import App
from saleor.plugins.manager import get_plugins_manager
from saleor.webhook.event_types import WebhookEventType
from saleor.webhook.models import Webhook


@pytest.fixture
def tax_line_data_response():
    return {
        "id": "1234",
        "currency": "PLN",
        "unit_net_amount": 12.34,
        "unit_gross_amount": 12.34,
        "total_gross_amount": 12.34,
        "total_net_amount": 12.34,
    }


@pytest.fixture
def tax_data_response(tax_line_data_response):
    return {
        "currency": "PLN",
        "total_net_amount": 12.34,
        "total_gross_amount": 12.34,
        "subtotal_net_amount": 12.34,
        "subtotal_gross_amount": 12.34,
        "shipping_price_gross_amount": 12.34,
        "shipping_price_net_amount": 12.34,
        "lines": [tax_line_data_response] * 5,
    }


@pytest.fixture
def tax_app(permission_handle_taxes):
    app = App.objects.create(name="Sample app objects", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_handle_taxes)
    return app


@pytest.fixture
def tax_checkout_webhook(tax_app):
    webhook = Webhook.objects.create(
        name="Tax checkout webhook",
        app=tax_app,
        target_url="https://www.example.com/tax-checkout",
    )
    webhook.events.create(event_type=WebhookEventType.CHECKOUT_CALCULATE_TAXES)
    return webhook


@pytest.fixture
def tax_order_webhook(tax_app):
    webhook = Webhook.objects.create(
        name="Tax order webhook",
        app=tax_app,
        target_url="https://www.example.com/tax-order",
    )
    webhook.events.create(event_type=WebhookEventType.ORDER_CALCULATE_TAXES)
    return webhook


@pytest.fixture
def webhook_plugin(settings):
    def factory():
        settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
        manager = get_plugins_manager()
        return manager.global_plugins[0]

    return factory
