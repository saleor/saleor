from unittest import mock

import pytest
import requests
from django.core.serializers import serialize

from saleor.extensions.manager import get_extensions_manager
from saleor.extensions.plugins.webhook import create_hmac_signature
from saleor.extensions.plugins.webhook.payloads import (
    generate_customer_payload,
    generate_order_payload,
    generate_product_payload,
)
from saleor.extensions.plugins.webhook.tasks import trigger_webhooks_for_event
from saleor.webhook import WebhookEventType


@pytest.mark.vcr
@mock.patch(
    "saleor.extensions.plugins.webhook.tasks.requests.post", wraps=requests.post
)
def test_trigger_webhooks_for_event(
    mock_request, webhook, order_with_lines, permission_manage_orders
):
    webhook.service_account.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/f0fc9979-cbd4-47b7-8705-1acb03fff1d0"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])

    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)

    expected_headers = {
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
    }

    mock_request.assert_called_once_with(
        webhook.target_url, data=expected_data, headers=expected_headers, timeout=10
    )


@pytest.mark.vcr
@mock.patch(
    "saleor.extensions.plugins.webhook.tasks.requests.post", wraps=requests.post
)
def test_trigger_webhooks_for_event_with_secret_key(
    mock_request, webhook, order_with_lines, permission_manage_orders
):
    webhook.service_account.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/f0fc9979-cbd4-47b7-8705-1acb03fff1d0"
    webhook.secret_key = "secret_key"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)

    expected_signature = create_hmac_signature(
        expected_data, webhook.secret_key, "utf-8"
    )
    expected_headers = {
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
        "X-Saleor-HMAC-SHA256": f"sha1={expected_signature}",
    }

    mock_request.assert_called_once_with(
        webhook.target_url, data=expected_data, headers=expected_headers, timeout=10
    )


@mock.patch("saleor.extensions.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_created(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.extensions.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_extensions_manager()
    manager.order_created(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_CREATED, expected_data
    )


@mock.patch("saleor.extensions.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_customer_created(mocked_webhook_trigger, settings, customer_user):
    settings.PLUGINS = ["saleor.extensions.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_extensions_manager()
    manager.customer_created(customer_user)

    expected_data = generate_customer_payload(customer_user)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.CUSTOMER_CREATED, expected_data
    )


@mock.patch("saleor.extensions.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_fully_paid(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.extensions.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_extensions_manager()
    manager.order_fully_paid(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_FULLYPAID, expected_data
    )


@mock.patch("saleor.extensions.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_product_created(mocked_webhook_trigger, settings, product):
    settings.PLUGINS = ["saleor.extensions.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_extensions_manager()
    manager.product_created(product)

    expected_data = generate_product_payload(product)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PRODUCT_CREATED, expected_data
    )


@mock.patch("saleor.extensions.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_updated(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.extensions.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_extensions_manager()
    manager.order_updated(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_UPDATED, expected_data
    )


@mock.patch("saleor.extensions.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_cancelled(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.extensions.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_extensions_manager()
    manager.order_cancelled(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_CANCELLED, expected_data
    )
