import uuid
from decimal import Decimal
from typing import List
from unittest import mock

import pytest

from saleor.app.models import App
from saleor.webhook.event_types import WebhookEventType
from saleor.webhook.models import Webhook, WebhookEvent

from ...base_plugin import ShippingMethod


@pytest.fixture()
def available_shipping_methods_factory():
    def factory(num_methods=1) -> List[ShippingMethod]:
        methods = []
        for i in range(num_methods):
            methods.append(
                ShippingMethod(
                    id=str(i),
                    price=Decimal("10.0"),
                    name=uuid.uuid4().hex,
                    maximum_order_weight=Decimal("0"),
                    minimum_order_weight=Decimal("100"),
                    maximum_delivery_days=Decimal("0"),
                    minimum_delivery_days=Decimal("5"),
                )
            )
        return methods

    return factory


@pytest.fixture
def shipping_app(db, permission_manage_orders, permission_manage_checkouts):
    app = App.objects.create(name="Shipping App", is_active=True)
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
                event_type=WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS,
                webhook=webhook,
            ),
            WebhookEvent(
                event_type=WebhookEventType.ORDER_FILTER_SHIPPING_METHODS,
                webhook=webhook,
            ),
        ]
    )
    return app


@mock.patch("saleor.plugins.webhook.plugin.send_webhook_request_sync")
def test_excluded_shipping_methods_for_order(
    mocked_webhook,
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
    shipping_app,
):
    # given
    reason = "spanish-inquisition"
    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": "1",
                "reason": reason,
            }
        ]
    }
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    # when
    excluded_methods = plugin.excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        previous_value=[],
    )
    # then
    assert len(excluded_methods) == 1
    em = excluded_methods[0]
    assert em.id == "1"
    assert em.reason == reason
    mocked_webhook.assert_called_once_with(
        mock.ANY, mock.ANY, WebhookEventType.ORDER_FILTER_SHIPPING_METHODS, mock.ANY
    )
