import json
from unittest import mock

import graphene
import pytest

from ....app.models import App
from ....webhook.event_types import WebhookEventType
from ....webhook.payloads import (
    generate_checkout_payload,
    generate_customer_payload,
    generate_invoice_payload,
    generate_order_payload,
    generate_page_payload,
    generate_product_deleted_payload,
    generate_product_payload,
    generate_product_variant_payload,
)
from ...manager import get_plugins_manager
from ...webhook.tasks import trigger_webhooks_for_event

first_url = "http://www.example.com/first/"
third_url = "http://www.example.com/third/"


@pytest.mark.parametrize(
    "event_name, total_webhook_calls, expected_target_urls",
    [
        (WebhookEventType.PRODUCT_CREATED, 1, {first_url}),
        (WebhookEventType.ORDER_FULLY_PAID, 2, {first_url, third_url}),
        (WebhookEventType.ORDER_FULFILLED, 1, {third_url}),
        (WebhookEventType.ORDER_CANCELLED, 1, {third_url}),
        (WebhookEventType.ORDER_CONFIRMED, 1, {third_url}),
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
def test_order_confirmed(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_confirmed(order_with_lines)

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.ORDER_CONFIRMED, expected_data
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
def test_customer_updated(mocked_webhook_trigger, settings, customer_user):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.customer_updated(customer_user)

    expected_data = generate_customer_payload(customer_user)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.CUSTOMER_UPDATED, expected_data
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
def test_product_updated(mocked_webhook_trigger, settings, product):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_updated(product)

    expected_data = generate_product_payload(product)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PRODUCT_UPDATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_product_deleted(mocked_webhook_trigger, settings, product):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()

    product = product
    variants_id = list(product.variants.all().values_list("id", flat=True))
    product_id = product.id
    product.delete()
    product.id = product_id
    variant_global_ids = [
        graphene.Node.to_global_id("ProductVariant", pk) for pk in variants_id
    ]
    manager.product_deleted(product, variants_id)

    expected_data = generate_product_deleted_payload(product, variants_id)

    expected_data_dict = json.loads(expected_data)[0]
    assert expected_data_dict["id"] is not None
    assert expected_data_dict["variants"] is not None
    assert variant_global_ids == expected_data_dict["variants"]

    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PRODUCT_DELETED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_product_variant_created(mocked_webhook_trigger, settings, variant):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_created(variant)

    expected_data = generate_product_variant_payload(variant)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PRODUCT_VARIANT_CREATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_product_variant_updated(mocked_webhook_trigger, settings, variant):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_updated(variant)

    expected_data = generate_product_variant_payload(variant)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PRODUCT_VARIANT_UPDATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_product_variant_deleted(mocked_webhook_trigger, settings, variant):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_deleted(variant)

    expected_data = generate_product_variant_payload(variant)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PRODUCT_VARIANT_DELETED, expected_data
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
def test_checkout_created(mocked_webhook_trigger, settings, checkout_with_items):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.checkout_created(checkout_with_items)

    expected_data = generate_checkout_payload(checkout_with_items)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.CHECKOUT_CREATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_checkout_updated(mocked_webhook_trigger, settings, checkout_with_items):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.checkout_updated(checkout_with_items)

    expected_data = generate_checkout_payload(checkout_with_items)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.CHECKOUT_UPADTED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_page_created(mocked_webhook_trigger, settings, page):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.page_created(page)

    expected_data = generate_page_payload(page)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PAGE_CREATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_page_updated(mocked_webhook_trigger, settings, page):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.page_updated(page)

    expected_data = generate_page_payload(page)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PAGE_UPDATED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_page_deleted(mocked_webhook_trigger, settings, page):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    page_id = page.id
    page.delete()
    page.id = page_id
    manager.page_deleted(page)

    expected_data = generate_page_payload(page)

    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.PAGE_DELETED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_invoice_request(mocked_webhook_trigger, settings, fulfilled_order):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_request(fulfilled_order, invoice, invoice.number)
    expected_data = generate_invoice_payload(invoice)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.INVOICE_REQUESTED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_invoice_delete(mocked_webhook_trigger, settings, fulfilled_order):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_delete(invoice)
    expected_data = generate_invoice_payload(invoice)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.INVOICE_DELETED, expected_data
    )


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_invoice_sent(mocked_webhook_trigger, settings, fulfilled_order):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_sent(invoice, fulfilled_order.user.email)
    expected_data = generate_invoice_payload(invoice)
    mocked_webhook_trigger.assert_called_once_with(
        WebhookEventType.INVOICE_SENT, expected_data
    )
