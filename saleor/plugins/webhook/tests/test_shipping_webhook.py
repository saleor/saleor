import json
import uuid
from decimal import Decimal
from typing import List
from unittest import mock

import graphene
import pytest

from ....app.models import App
from ....webhook.event_types import WebhookEventType
from ....webhook.models import Webhook, WebhookEvent
from ....webhook.payloads import (
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
)
from ...base_plugin import ExcludedShippingMethod, ShippingMethod


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
@mock.patch(
    "saleor.plugins.webhook.plugin.generate_excluded_shipping_methods_for_order_payload"
)
def test_excluded_shipping_methods_for_order(
    mocked_payload,
    mocked_webhook,
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
    shipping_app,
):
    # given
    webhook_reason = "spanish-inquisition"
    other_reason = "it's a trap"
    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": "1",
                "reason": webhook_reason,
            }
        ]
    }
    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = [
        ExcludedShippingMethod(id="1", reason=other_reason),
        ExcludedShippingMethod(id="2", reason=other_reason),
    ]

    # when
    excluded_methods = plugin.excluded_shipping_methods_for_order(
        order=order_with_lines,
        available_shipping_methods=available_shipping_methods,
        previous_value=previous_value,
    )
    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert other_reason in em.reason
    mocked_webhook.assert_called_once_with(
        mock.ANY, mock.ANY, WebhookEventType.ORDER_FILTER_SHIPPING_METHODS, payload
    )


@mock.patch("saleor.plugins.webhook.plugin.send_webhook_request_sync")
@mock.patch(
    "saleor.plugins.webhook.plugin."
    "generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
    shipping_app,
):
    # given
    webhook_reason = "spanish-inquisition"
    other_reason = "it's a trap"
    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": "1",
                "reason": webhook_reason,
            }
        ]
    }
    payload = mock.MagicMock()
    mocked_payload.return_value = payload
    plugin = webhook_plugin()
    available_shipping_methods = available_shipping_methods_factory(num_methods=2)
    previous_value = [
        ExcludedShippingMethod(id="1", reason=other_reason),
        ExcludedShippingMethod(id="2", reason=other_reason),
    ]
    # when
    excluded_methods = plugin.excluded_shipping_methods_for_checkout(
        checkout=checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        previous_value=previous_value,
    )
    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert other_reason in em.reason
    mocked_webhook.assert_called_once_with(
        mock.ANY, mock.ANY, WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS, payload
    )


def test_generate_excluded_shipping_methods_for_order_payload(
    webhook_plugin,
    order_with_lines,
    available_shipping_methods_factory,
):
    # given
    methods = available_shipping_methods_factory(num_methods=3)
    # when
    json_payload = json.loads(
        generate_excluded_shipping_methods_for_order_payload(
            order=order_with_lines, available_shipping_methods=methods
        )
    )
    # then
    assert len(json_payload["shipping_methods"]) == 3
    assert json_payload["shipping_methods"][0]["id"] == methods[0].id
    assert json_payload["shipping_methods"][1]["id"] == methods[1].id
    assert json_payload["shipping_methods"][2]["id"] == methods[2].id
    graphql_order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    assert json_payload["order"]["id"] == graphql_order_id


def test_generate_excluded_shipping_methods_for_checkout_payload(
    webhook_plugin,
    checkout_with_items,
    available_shipping_methods_factory,
):
    # given
    methods = available_shipping_methods_factory(num_methods=3)
    # when
    json_payload = json.loads(
        generate_excluded_shipping_methods_for_checkout_payload(
            checkout=checkout_with_items, available_shipping_methods=methods
        )
    )
    # then
    assert len(json_payload["shipping_methods"]) == 3
    assert json_payload["shipping_methods"][0]["id"] == methods[0].id
    assert json_payload["shipping_methods"][1]["id"] == methods[1].id
    assert json_payload["shipping_methods"][2]["id"] == methods[2].id
    assert "checkout" in json_payload
