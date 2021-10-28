import json
from unittest import mock
from unittest.mock import ANY, MagicMock
from urllib.parse import urlencode

import boto3
import graphene
import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core.serializers import serialize
from freezegun import freeze_time
from kombu.asynchronous.aws.sqs.connection import AsyncSQSConnection

from ....account.notifications import (
    get_default_user_payload,
    send_account_confirmation,
)
from ....app.models import App
from ....core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ....core.notifications import get_site_context
from ....core.notify_events import NotifyEventType
from ....core.utils.json_serializer import CustomJsonEncoder
from ....core.utils.url import prepare_url
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
from ...webhook.plugin import WebhookPlugin
from ...webhook.tasks import send_webhook_request

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
    event_payload = EventPayload.objects.create()
    WebhookPlugin._trigger_webhook_requests(event_payload, event_name)
    deliveries_called = {
        EventDelivery.objects.get(id=delivery_id[0][0])
        for delivery_id in mock_request.call_args_list
    }
    urls_called = {delivery.webhook.target_url for delivery in deliveries_called}
    assert mock_request.call_count == total_webhook_calls
    assert urls_called == expected_target_urls


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_order_created(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_created(order_with_lines)

    event_payload = EventPayload.objects.first()
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.ORDER_CREATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_order_confirmed(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_confirmed(order_with_lines)

    event_payload = EventPayload.objects.first()
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.ORDER_CONFIRMED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_draft_order_created(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.draft_order_created(order_with_lines)

    event_payload = EventPayload.objects.first()
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.DRAFT_ORDER_CREATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_draft_order_deleted(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.draft_order_deleted(order_with_lines)
    event_payload = EventPayload.objects.first()

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.DRAFT_ORDER_DELETED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_draft_order_updated(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.draft_order_updated(order_with_lines)
    event_payload = EventPayload.objects.first()

    expected_data = generate_order_payload(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.DRAFT_ORDER_UPDATED
    )

    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_customer_created(mocked_webhook_trigger, settings, customer_user):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.customer_created(customer_user)

    event_payload = EventPayload.objects.first()
    expected_data = generate_customer_payload(customer_user)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.CUSTOMER_CREATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_customer_updated(mocked_webhook_trigger, settings, customer_user):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.customer_updated(customer_user)

    event_payload = EventPayload.objects.first()
    expected_data = generate_customer_payload(customer_user)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.CUSTOMER_UPDATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_order_fully_paid(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_fully_paid(order_with_lines)

    event_payload = EventPayload.objects.first()
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.ORDER_FULLY_PAID
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_product_created(mocked_webhook_trigger, settings, product):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_created(product)

    event_payload = EventPayload.objects.first()
    expected_data = generate_product_payload(product)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PRODUCT_CREATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_product_updated(mocked_webhook_trigger, settings, product):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_updated(product)

    event_payload = EventPayload.objects.first()
    expected_data = generate_product_payload(product)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PRODUCT_UPDATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
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
    event_payload = EventPayload.objects.first()

    expected_data_dict = json.loads(expected_data)[0]
    assert expected_data_dict["id"] is not None
    assert expected_data_dict["variants"] is not None
    assert variant_global_ids == expected_data_dict["variants"]

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PRODUCT_DELETED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_product_variant_created(mocked_webhook_trigger, settings, variant):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_created(variant)

    event_payload = EventPayload.objects.first()
    expected_data = generate_product_variant_payload([variant])

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PRODUCT_VARIANT_CREATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_product_variant_updated(mocked_webhook_trigger, settings, variant):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_updated(variant)

    event_payload = EventPayload.objects.first()
    expected_data = generate_product_variant_payload([variant])

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PRODUCT_VARIANT_UPDATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_product_variant_deleted(mocked_webhook_trigger, settings, variant):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_deleted(variant)

    event_payload = EventPayload.objects.first()
    expected_data = generate_product_variant_payload([variant])

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PRODUCT_VARIANT_DELETED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_order_updated(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_updated(order_with_lines)

    event_payload = EventPayload.objects.first()
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.ORDER_UPDATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_order_cancelled(mocked_webhook_trigger, settings, order_with_lines):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_cancelled(order_with_lines)

    event_payload = EventPayload.objects.first()
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.ORDER_CANCELLED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_checkout_created(mocked_webhook_trigger, settings, checkout_with_items):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.checkout_created(checkout_with_items)

    event_payload = EventPayload.objects.first()
    expected_data = generate_checkout_payload(checkout_with_items)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.CHECKOUT_CREATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_checkout_updated(mocked_webhook_trigger, settings, checkout_with_items):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.checkout_updated(checkout_with_items)

    event_payload = EventPayload.objects.first()
    expected_data = generate_checkout_payload(checkout_with_items)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.CHECKOUT_UPDATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_page_created(mocked_webhook_trigger, settings, page):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.page_created(page)

    event_payload = EventPayload.objects.first()
    expected_data = generate_page_payload(page)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PAGE_CREATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_page_updated(mocked_webhook_trigger, settings, page):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.page_updated(page)

    event_payload = EventPayload.objects.first()
    expected_data = generate_page_payload(page)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PAGE_UPDATED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_page_deleted(mocked_webhook_trigger, settings, page):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    page_id = page.id
    page.delete()
    page.id = page_id
    manager.page_deleted(page)

    expected_data = generate_page_payload(page)
    event_payload = EventPayload.objects.first()

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.PAGE_DELETED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_invoice_request(mocked_webhook_trigger, settings, fulfilled_order):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_request(fulfilled_order, invoice, invoice.number)

    event_payload = EventPayload.objects.first()
    expected_data = generate_invoice_payload(invoice)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.INVOICE_REQUESTED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_invoice_delete(mocked_webhook_trigger, settings, fulfilled_order):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_delete(invoice)

    event_payload = EventPayload.objects.first()
    expected_data = generate_invoice_payload(invoice)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.INVOICE_DELETED
    )
    assert expected_data == event_payload.payload


@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_invoice_sent(mocked_webhook_trigger, settings, fulfilled_order):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_sent(invoice, fulfilled_order.user.email)

    event_payload = EventPayload.objects.first()
    expected_data = generate_invoice_payload(invoice)

    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.INVOICE_SENT
    )
    assert expected_data == event_payload.payload


@freeze_time("2020-03-18 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.WebhookPlugin._trigger_webhook_requests")
def test_notify_user(mocked_webhook_trigger, settings, customer_user, channel_USD):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()

    redirect_url = "http://redirect.com/"
    send_account_confirmation(customer_user, redirect_url, manager, channel_USD.slug)

    token = default_token_generator.make_token(customer_user)
    params = urlencode({"email": customer_user.email, "token": token})
    confirm_url = prepare_url(params, redirect_url)

    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": customer_user.email,
        "token": token,
        "confirm_url": confirm_url,
        "channel_slug": channel_USD.slug,
        **get_site_context(),
    }

    event_payload = EventPayload.objects.first()
    expected_data = {
        "notify_event": NotifyEventType.ACCOUNT_CONFIRMATION,
        "payload": payload,
    }
    mocked_webhook_trigger.assert_called_once_with(
        event_payload, WebhookEventType.NOTIFY_USER
    )
    assert json.dumps(expected_data, cls=CustomJsonEncoder) == event_payload.payload


def test_create_event_payload_reference_with_error(
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
):
    mocked_client = MagicMock(spec=AsyncSQSConnection)
    mocked_client_constructor = MagicMock(spec=boto3.client, return_value=mocked_client)

    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.boto3.client",
        mocked_client_constructor,
    )

    webhook.app.permissions.add(permission_manage_orders)

    webhook.target_url = "testy"
    webhook.save()
    expected_data = serialize("json", [order_with_lines])
    event_payload = EventPayload.objects.create(payload=expected_data)
    WebhookPlugin._trigger_webhook_requests(
        event_payload, WebhookEventType.ORDER_CREATED
    )
    delivery = EventDelivery.objects.first()
    send_webhook_request(delivery.id)
    attempt = EventDeliveryAttempt.objects.first()

    assert delivery.webhook == webhook
    assert delivery.event_type == WebhookEventType.ORDER_CREATED
    assert attempt.response == "Unknown webhook scheme: ''"
    assert delivery.status == "failed"
    assert attempt.task_id == ANY
    assert attempt.duration == ANY
