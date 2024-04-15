import uuid
from decimal import Decimal

import pytest
from measurement.measures import Weight
from prices import Money

from ....app.models import App
from ....plugins.manager import get_plugins_manager
from ....plugins.webhook.plugin import WebhookPlugin
from ....shipping.interface import ShippingMethodData
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook, WebhookEvent


@pytest.fixture
def webhook_plugin(settings):
    def factory() -> WebhookPlugin:
        settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
        manager = get_plugins_manager(allow_replica=False)
        manager.get_all_plugins()
        return manager.global_plugins[0]

    return factory


@pytest.fixture
def available_shipping_methods_factory():
    def factory(num_methods=1) -> list[ShippingMethodData]:
        methods = []
        for i in range(num_methods):
            methods.append(
                ShippingMethodData(
                    id=str(i),
                    price=Money(Decimal("10"), "usd"),
                    name=uuid.uuid4().hex,
                    maximum_order_weight=Weight(kg=0),
                    minimum_order_weight=Weight(kg=0),
                    maximum_delivery_days=0,
                    minimum_delivery_days=5,
                )
            )
        return methods

    return factory


@pytest.fixture
def shipping_app_factory(db, permission_manage_orders, permission_manage_checkouts):
    def create_app(app_name="Shipping App"):
        app = App.objects.create(name=app_name, is_active=True)
        app.tokens.create(name="Default")
        app.permissions.add(permission_manage_orders)
        app.permissions.add(permission_manage_checkouts)

        webhook = Webhook.objects.create(
            name="shipping-webhook-1",
            app=app,
            target_url="https://shipping-gateway.com/api/",
        )
        webhook.events.bulk_create(
            [
                WebhookEvent(
                    event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                    webhook=webhook,
                ),
                WebhookEvent(
                    event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
                    webhook=webhook,
                ),
            ]
        )
        return app

    return create_app
