import json
from datetime import datetime
from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, MagicMock
from urllib.parse import urlencode

import boto3
import graphene
import pytest
from celery.exceptions import MaxRetriesExceededError
from celery.exceptions import Retry as CeleryTaskRetryError
from django.contrib.auth.tokens import default_token_generator
from django.core.serializers import serialize
from django.utils import timezone
from freezegun import freeze_time
from kombu.asynchronous.aws.sqs.connection import AsyncSQSConnection

from .... import __version__
from ....account.notifications import (
    get_default_user_payload,
    send_account_confirmation,
)
from ....app.models import App
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ....core.notification.utils import get_site_context
from ....core.notify_events import NotifyEventType
from ....core.utils.url import prepare_url
from ....discount.utils import fetch_catalogue_info
from ....graphql.discount.mutations import convert_catalogue_info_to_global_ids
from ....payment import TransactionAction
from ....payment.interface import TransactionActionData
from ....payment.models import TransactionItem
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import (
    generate_checkout_payload,
    generate_collection_payload,
    generate_customer_payload,
    generate_invoice_payload,
    generate_order_payload,
    generate_page_payload,
    generate_product_deleted_payload,
    generate_product_payload,
    generate_product_variant_payload,
    generate_product_variant_with_stock_payload,
    generate_sale_payload,
    generate_transaction_action_request_payload,
)
from ....webhook.utils import get_webhooks_for_event
from ...manager import get_plugins_manager
from ...webhook.tasks import send_webhook_request_async, trigger_webhooks_async

first_url = "http://www.example.com/first/"
third_url = "http://www.example.com/third/"


@pytest.mark.parametrize(
    "event_name, total_webhook_calls, expected_target_urls",
    [
        (WebhookEventAsyncType.PRODUCT_CREATED, 1, {first_url}),
        (WebhookEventAsyncType.ORDER_FULLY_PAID, 2, {first_url, third_url}),
        (WebhookEventAsyncType.ORDER_FULFILLED, 1, {third_url}),
        (WebhookEventAsyncType.ORDER_CANCELLED, 1, {third_url}),
        (WebhookEventAsyncType.ORDER_CONFIRMED, 1, {third_url}),
        (WebhookEventAsyncType.ORDER_UPDATED, 1, {third_url}),
        (WebhookEventAsyncType.ORDER_CREATED, 1, {third_url}),
        (WebhookEventAsyncType.CUSTOMER_CREATED, 0, set()),
    ],
)
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async.delay")
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
    webhook.events.create(event_type=WebhookEventAsyncType.CUSTOMER_CREATED)
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_CREATED)
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_FULLY_PAID)

    app_without_permissions = App.objects.create()

    second_webhook = app_without_permissions.webhooks.create(
        target_url="http://www.example.com/wrong"
    )
    second_webhook.events.create(event_type=WebhookEventAsyncType.ANY)
    second_webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_CREATED)
    second_webhook.events.create(event_type=WebhookEventAsyncType.CUSTOMER_CREATED)

    app_with_partial_permissions = App.objects.create()
    app_with_partial_permissions.permissions.add(permission_manage_orders)
    third_webhook = app_with_partial_permissions.webhooks.create(
        target_url="http://www.example.com/third/"
    )
    third_webhook.events.create(event_type=WebhookEventAsyncType.ANY)
    event_payload = EventPayload.objects.create()
    trigger_webhooks_async(
        event_payload, event_name, get_webhooks_for_event(event_name)
    )
    deliveries_called = {
        EventDelivery.objects.get(id=delivery_id[0][0])
        for delivery_id in mock_request.call_args_list
    }
    urls_called = {delivery.webhook.target_url for delivery in deliveries_called}
    assert mock_request.call_count == total_webhook_calls
    assert urls_called == expected_target_urls


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_created(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_confirmed(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_confirmed(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_draft_order_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.draft_order_created(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_draft_order_deleted(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.draft_order_deleted(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.DRAFT_ORDER_DELETED,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_draft_order_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.draft_order_updated(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    customer_user,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.customer_created(customer_user)
    expected_data = generate_customer_payload(customer_user)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.CUSTOMER_CREATED,
        [any_webhook],
        customer_user,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    customer_user,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.customer_updated(customer_user)
    expected_data = generate_customer_payload(customer_user)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.CUSTOMER_UPDATED,
        [any_webhook],
        customer_user,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_fully_paid(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_fully_paid(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_collection_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    collection,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.collection_created(collection)
    expected_data = generate_collection_payload(collection)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.COLLECTION_CREATED,
        [any_webhook],
        collection,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_collection_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    collection,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.collection_updated(collection)
    expected_data = generate_collection_payload(collection)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.COLLECTION_UPDATED,
        [any_webhook],
        collection,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_collection_deleted(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    collection,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.collection_deleted(collection)
    expected_data = generate_collection_payload(collection)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.COLLECTION_DELETED,
        [any_webhook],
        collection,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    product,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_created(product)
    expected_data = generate_product_payload(product)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_CREATED,
        [any_webhook],
        product,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    product,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_updated(product)
    expected_data = generate_product_payload(product)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_UPDATED,
        [any_webhook],
        product,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_deleted(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    product,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
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
        expected_data,
        WebhookEventAsyncType.PRODUCT_DELETED,
        [any_webhook],
        product,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    variant,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_created(variant)
    expected_data = generate_product_variant_payload([variant])

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_VARIANT_CREATED,
        [any_webhook],
        variant,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    variant,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_updated(variant)
    expected_data = generate_product_variant_payload([variant])

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        [any_webhook],
        variant,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_deleted(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    variant,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_deleted(variant)
    expected_data = generate_product_variant_payload([variant])

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_VARIANT_DELETED,
        [any_webhook],
        variant,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_out_of_stock(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    variant_with_many_stocks,
):
    variant = variant_with_many_stocks.stocks.first()
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_out_of_stock(variant)

    expected_data = generate_product_variant_with_stock_payload([variant])
    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK,
        [any_webhook],
        variant,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_back_in_stock(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    variant_with_many_stocks,
):
    variant = variant_with_many_stocks.stocks.first()
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.product_variant_back_in_stock(variant)

    expected_data = generate_product_variant_with_stock_payload([variant])
    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK,
        [any_webhook],
        variant,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_updated(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.ORDER_UPDATED,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_cancelled(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.order_cancelled(order_with_lines)
    expected_data = generate_order_payload(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.ORDER_CANCELLED,
        [any_webhook],
        order_with_lines,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_checkout_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    checkout_with_items,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.checkout_created(checkout_with_items)
    expected_data = generate_checkout_payload(checkout_with_items)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.CHECKOUT_CREATED,
        [any_webhook],
        checkout_with_items,
        None,
    )


def test_checkout_payload_includes_sales(checkout_with_item, sale, discount_info):
    data = json.loads(generate_checkout_payload(checkout_with_item))
    variant = checkout_with_item.lines.first().variant
    channel_listing = variant.channel_listings.first()
    variant_price_with_sale = variant.get_price(
        product=variant.product,
        collections=[],
        channel=checkout_with_item.channel,
        channel_listing=channel_listing,
        discounts=[discount_info],
    )
    variant_price_without_sale = variant.get_price(
        product=variant.product,
        collections=[],
        channel=checkout_with_item.channel,
        channel_listing=channel_listing,
        discounts=[],
    )
    assert variant_price_without_sale > variant_price_with_sale
    assert Decimal(data[0]["lines"][0]["base_price"]) == variant_price_with_sale.amount


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_checkout_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    checkout_with_items,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.checkout_updated(checkout_with_items)
    expected_data = generate_checkout_payload(checkout_with_items)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.CHECKOUT_UPDATED,
        [any_webhook],
        checkout_with_items,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_created(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, page
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.page_created(page)
    expected_data = generate_page_payload(page)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.PAGE_CREATED, [any_webhook], page, None
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_updated(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, page
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    manager.page_updated(page)
    expected_data = generate_page_payload(page)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.PAGE_UPDATED, [any_webhook], page, None
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_deleted(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, page
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    page_id = page.id
    page.delete()
    page.id = page_id
    manager.page_deleted(page)
    expected_data = generate_page_payload(page)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.PAGE_DELETED, [any_webhook], page, None
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_invoice_request(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    fulfilled_order,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_request(fulfilled_order, invoice, invoice.number)
    expected_data = generate_invoice_payload(invoice)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.INVOICE_REQUESTED,
        [any_webhook],
        invoice,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_invoice_delete(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    fulfilled_order,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_delete(invoice)
    expected_data = generate_invoice_payload(invoice)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.INVOICE_DELETED,
        [any_webhook],
        invoice,
        None,
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_invoice_sent(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    fulfilled_order,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    invoice = fulfilled_order.invoices.first()
    manager.invoice_sent(invoice, fulfilled_order.user.email)
    expected_data = generate_invoice_payload(invoice)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.INVOICE_SENT, [any_webhook], invoice, None
    )


@freeze_time("2020-03-18 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_notify_user(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    customer_user,
    channel_USD,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(lambda: customer_user)
    timestamp = timezone.make_aware(
        datetime.strptime("2020-03-18 12:00", "%Y-%m-%d %H:%M"), timezone.utc
    ).isoformat()

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
    data = {
        "notify_event": NotifyEventType.ACCOUNT_CONFIRMATION,
        "payload": payload,
        "meta": {
            "issued_at": timestamp,
            "version": __version__,
            "issuing_principal": {
                "id": graphene.Node.to_global_id("User", customer_user.id),
                "type": "user",
            },
        },
    }
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(data), WebhookEventAsyncType.NOTIFY_USER, [any_webhook]
    )


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
    trigger_webhooks_async(
        event_payload, WebhookEventAsyncType.ORDER_CREATED, [webhook]
    )
    delivery = EventDelivery.objects.first()
    send_webhook_request_async(delivery.id)
    attempt = EventDeliveryAttempt.objects.first()

    assert delivery.webhook == webhook
    assert delivery.event_type == WebhookEventAsyncType.ORDER_CREATED
    assert attempt.response == "Unknown webhook scheme: ''"
    assert delivery.status == "failed"
    assert attempt.task_id == ANY
    assert attempt.duration == ANY


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_created(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, sale
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    sale_catalogue_info = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    manager.sale_created(sale, current_catalogue=sale_catalogue_info)
    expected_data = generate_sale_payload(sale, current_catalogue=sale_catalogue_info)
    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.SALE_CREATED, [any_webhook], sale, None
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    sale,
    product_list,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    previous_sale_catalogue_info = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    sale.products.add(*product_list)
    current_sale_catalogue_info = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )

    manager.sale_updated(
        sale,
        previous_catalogue=previous_sale_catalogue_info,
        current_catalogue=current_sale_catalogue_info,
    )
    expected_data = generate_sale_payload(
        sale,
        current_catalogue=current_sale_catalogue_info,
        previous_catalogue=previous_sale_catalogue_info,
    )
    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.SALE_UPDATED, [any_webhook], sale, None
    )


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_deleted(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, sale
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    sale_catalogue_info = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    manager.sale_deleted(sale, previous_catalogue=sale_catalogue_info)
    expected_data = generate_sale_payload(sale, previous_catalogue=sale_catalogue_info)
    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.SALE_DELETED, [any_webhook], sale, None
    )


@mock.patch("saleor.plugins.webhook.plugin.send_webhook_request_async.delay")
def test_event_delivery_retry(mocked_webhook_send, event_delivery, settings):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()

    # when
    manager.event_delivery_retry(event_delivery)

    # then
    mocked_webhook_send.assert_called_once_with(event_delivery.pk)


@mock.patch("saleor.plugins.webhook.tasks.clear_successful_delivery")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_using_scheme_method")
def test_send_webhook_request_async(
    mocked_send_response, mocked_clear_delivery, event_delivery, webhook_response
):
    mocked_send_response.return_value = webhook_response
    send_webhook_request_async(event_delivery.pk)

    mocked_send_response.assert_called_once_with(
        event_delivery.webhook.target_url,
        "mirumee.com",
        event_delivery.webhook.secret_key,
        event_delivery.event_type,
        event_delivery.payload.payload,
    )
    mocked_clear_delivery.assert_called_once_with(event_delivery)
    attempt = EventDeliveryAttempt.objects.filter(delivery=event_delivery).first()
    delivery = EventDelivery.objects.get(id=event_delivery.pk)
    assert attempt.status == EventDeliveryStatus.SUCCESS
    assert attempt.response == webhook_response.content
    assert attempt.response_headers == json.dumps(webhook_response.response_headers)
    assert attempt.response_status_code == webhook_response.response_status_code
    assert attempt.request_headers == json.dumps(webhook_response.request_headers)
    assert attempt.duration == webhook_response.duration
    assert delivery.status == EventDeliveryStatus.SUCCESS


@mock.patch("saleor.plugins.webhook.tasks.clear_successful_delivery")
def test_send_webhook_request_async_when_webhook_is_disabled(
    mocked_clear_delivery, event_delivery
):
    # given
    event_delivery.webhook.is_active = False
    event_delivery.webhook.save(update_fields=["is_active"])

    # when
    send_webhook_request_async(event_delivery.pk)
    event_delivery.refresh_from_db()

    # then
    mocked_clear_delivery.not_called()
    assert event_delivery.status == EventDeliveryStatus.FAILED


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_transaction_action_request(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order,
    channel_USD,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager()
    transaction = TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )
    action_value = Decimal("5.00")
    transaction_action_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.CAPTURE,
        action_value=action_value,
    )

    # when
    manager.transaction_action_request(
        transaction_action_data, channel_slug=channel_USD.slug
    )

    # then
    expected_data = generate_transaction_action_request_payload(
        transaction_action_data,
    )
    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST,
        [any_webhook],
        subscribable_object=transaction_action_data,
        requestor=ANY,
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_using_scheme_method")
def test_send_webhook_request_async_when_delivery_attempt_failed(
    mocked_send_response,
    event_delivery,
    webhook_response_failed,
):
    mocked_send_response.return_value = webhook_response_failed

    with pytest.raises(CeleryTaskRetryError):
        send_webhook_request_async(event_delivery.pk)

    attempt = EventDeliveryAttempt.objects.filter(delivery=event_delivery).first()
    delivery = EventDelivery.objects.get(id=event_delivery.pk)
    assert attempt.status == EventDeliveryStatus.FAILED
    assert attempt.response_status_code == webhook_response_failed.response_status_code
    assert delivery.status == EventDeliveryStatus.PENDING


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async.retry")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_using_scheme_method")
def test_send_webhook_request_async_when_max_retries_exceeded(
    mocked_send_response,
    mocked_task_retry,
    event_delivery,
    webhook_response_failed,
):
    mocked_send_response.return_value = webhook_response_failed
    mocked_task_retry.side_effect = MaxRetriesExceededError()

    send_webhook_request_async(event_delivery.pk)

    attempt = EventDeliveryAttempt.objects.filter(delivery=event_delivery).first()
    delivery = EventDelivery.objects.get(id=event_delivery.pk)
    assert attempt.status == EventDeliveryStatus.FAILED
    assert delivery.status == EventDeliveryStatus.FAILED


@pytest.mark.parametrize(
    "event, expected_is_active",
    (("invoice_request", False), ("transaction_action_request", True)),
)
def test_is_event_active(
    event, expected_is_active, settings, webhook, permission_manage_payments
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook.app.permissions.add(permission_manage_payments)
    webhook.events.create(event_type=WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST)

    manager = get_plugins_manager()

    # when
    is_active = manager.is_event_active_for_any_plugin(event)

    # then
    assert is_active == expected_is_active
