from unittest import mock

import pytest
import requests
from django.core.serializers import serialize

from saleor.app.models import App
from saleor.plugins.manager import get_plugins_manager
from saleor.plugins.webhook import create_hmac_signature
from saleor.plugins.webhook.tasks import trigger_webhooks_for_event
from saleor.webhook.event_types import WebhookEventType
from saleor.webhook.payloads import (
    generate_checkout_payload,
    generate_customer_payload,
    generate_order_payload,
    generate_product_payload,
)


@pytest.mark.vcr
@mock.patch("saleor.plugins.webhook.tasks.requests.post", wraps=requests.post)
def test_trigger_webhooks_for_event(
    mock_request,
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
):
    webhook.app.permissions.add(permission_manage_orders)
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


first_url = "http://www.example.com/first/"
third_url = "http://www.example.com/third/"


@pytest.mark.parametrize(
    "event_name, total_webhook_calls, expected_target_urls",
    [
        (WebhookEventType.PRODUCT_CREATED, 1, {first_url}),
        (WebhookEventType.ORDER_FULLY_PAID, 2, {first_url, third_url}),
        (WebhookEventType.ORDER_FULFILLED, 1, {third_url}),
        (WebhookEventType.ORDER_CANCELLED, 1, {third_url}),
        (WebhookEventType.ORDER_UPDATED, 1, {third_url}),
        (WebhookEventType.ORDER_CREATED, 1, {third_url}),
        (WebhookEventType.CUSTOMER_CREATED, 0, set()),
    ],
)
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request.delay")
def test_trigger_webhooks_for_event_calls_expected_events(
    mock_request,
    event_name,
    total_webhook_calls,
    expected_target_urls,
    app,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
):
    """Confirm that Saleor executes only valid and allowed webhook events."""

    app.permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_products)
    webhook = app.webhooks.create(target_url="http://www.example.com/first/")
    webhook.events.create(event_type=WebhookEventType.CUSTOMER_CREATED)
    webhook.events.create(event_type=WebhookEventType.PRODUCT_CREATED)
    webhook.events.create(event_type=WebhookEventType.ORDER_FULLY_PAID)

    app_without_permissions = App.objects.create()

    second_webhook = app_without_permissions.webhooks.create(
        target_url="http://www.example.com/wrong"
    )
    second_webhook.events.create(event_type=WebhookEventType.ANY)
    second_webhook.events.create(event_type=WebhookEventType.PRODUCT_CREATED)
    second_webhook.events.create(event_type=WebhookEventType.CUSTOMER_CREATED)

    app_with_partial_permissions = App.objects.create()
    app_with_partial_permissions.permissions.add(permission_manage_orders)
    third_webhook = app_with_partial_permissions.webhooks.create(
        target_url="http://www.example.com/third/"
    )
    third_webhook.events.create(event_type=WebhookEventType.ANY)

    trigger_webhooks_for_event(event_name, data="")
    assert mock_request.call_count == total_webhook_calls

    target_url_calls = {call[0][1] for call in mock_request.call_args_list}
    assert target_url_calls == expected_target_urls


@pytest.mark.vcr
@mock.patch("saleor.plugins.webhook.tasks.requests.post", wraps=requests.post)
def test_trigger_webhooks_for_event_with_secret_key(
    mock_request, webhook, order_with_lines, permission_manage_orders
):
    webhook.app.permissions.add(permission_manage_orders)
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


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_created(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_created(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_CREATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_customer_created(mocked_webhook_trigger, settings, customer_user):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.customer_created(customer_user)

    expected_data = generate_customer_payload(customer_user)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.CUSTOMER_CREATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_fully_paid(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_fully_paid(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_FULLY_PAID, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_product_created(mocked_webhook_trigger, settings, product):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_created(product)

    expected_data = generate_product_payload(product)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PRODUCT_CREATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_updated(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_updated(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_UPDATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_order_cancelled(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_cancelled(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_CANCELLED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_checkout_quantity_changed(
    mocked_webhook_trigger, settings, checkout_with_items
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.checkout_quantity_changed(checkout_with_items)

    expected_data = generate_checkout_payload(checkout_with_items)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.CHECKOUT_QUANTITY_CHANGED, expected_data
    )
