import datetime
import json
from decimal import Decimal
from functools import partial
from unittest import mock
from unittest.mock import ANY, MagicMock
from urllib.parse import urlencode

import boto3
import graphene
import pytest
from celery.exceptions import MaxRetriesExceededError
from celery.exceptions import Retry as CeleryTaskRetryError
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core.serializers import serialize
from freezegun import freeze_time
from kombu.asynchronous.aws.sqs.connection import AsyncSQSConnection
from requests import RequestException
from requests_hardened import HTTPSession

from .... import __version__
from ....account.notifications import (
    get_default_user_payload,
    send_account_confirmation,
)
from ....app.models import App
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ....core.notification.utils import get_site_context
from ....core.notify import NotifyEventType
from ....core.utils.url import prepare_url
from ....discount import RewardType, RewardValueType
from ....discount.interface import VariantPromotionRuleInfo
from ....discount.utils.checkout import (
    create_or_update_discount_objects_from_promotion_for_checkout,
)
from ....graphql.discount.enums import DiscountValueTypeEnum
from ....graphql.discount.utils import convert_migrated_sale_predicate_to_catalogue_info
from ....graphql.order.tests.mutations.test_order_discount import ORDER_DISCOUNT_ADD
from ....graphql.product.tests.mutations.test_product_create import (
    CREATE_PRODUCT_MUTATION,
)
from ....payment import TransactionAction, TransactionEventType
from ....payment.interface import TransactionActionData
from ....payment.models import TransactionItem
from ....site.models import SiteSettings
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.payloads import (
    generate_checkout_payload,
    generate_product_deleted_payload,
)
from ....webhook.transport import signature_for_payload
from ....webhook.transport.asynchronous.transport import (
    WebhookPayloadData,
    send_webhook_request_async,
    trigger_webhooks_async,
)
from ....webhook.utils import get_webhooks_for_event
from ...manager import get_plugins_manager
from .utils import generate_request_headers

first_url = "http://www.example.com/first/"
third_url = "http://www.example.com/third/"


@pytest.mark.parametrize(
    ("event_name", "total_webhook_calls", "expected_target_urls"),
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
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
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
    payload = ""
    trigger_webhooks_async(
        payload,
        event_name,
        get_webhooks_for_event(event_name),
        allow_replica=False,
    )

    deliveries_called = {
        EventDelivery.objects.get(id=request.kwargs["kwargs"]["event_delivery_id"])
        for request in mock_request.call_args_list
    }
    urls_called = {delivery.webhook.target_url for delivery in deliveries_called}
    assert mock_request.call_count == total_webhook_calls
    assert urls_called == expected_target_urls


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
    manager = get_plugins_manager(allow_replica=False)
    manager.order_created(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_CREATED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.order_confirmed(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.draft_order_created(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.draft_order_deleted(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.DRAFT_ORDER_DELETED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.draft_order_updated(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.customer_created(customer_user)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.CUSTOMER_CREATED,
        [any_webhook],
        customer_user,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.customer_updated(customer_user)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.CUSTOMER_UPDATED,
        [any_webhook],
        customer_user,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    customer_user,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.customer_metadata_updated(customer_user)
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED,
        [any_webhook],
        customer_user,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.order_fully_paid(order_with_lines)
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_paid(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.order_paid(order_with_lines)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_PAID,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_refunded(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.order_refunded(order_with_lines)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_REFUNDED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_fully_refunded(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.order_fully_refunded(order_with_lines)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.collection_created(collection)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.COLLECTION_CREATED,
        [any_webhook],
        collection,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.collection_updated(collection)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.COLLECTION_UPDATED,
        [any_webhook],
        collection,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.collection_deleted(collection)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.COLLECTION_DELETED,
        [any_webhook],
        collection,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_collection_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    collection,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.collection_metadata_updated(collection)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.COLLECTION_METADATA_UPDATED,
        [any_webhook],
        collection,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.product_created(product)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_CREATED,
        [any_webhook],
        product,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.product_updated(product)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_UPDATED,
        [any_webhook],
        product,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)

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
        None,
        WebhookEventAsyncType.PRODUCT_DELETED,
        [any_webhook],
        product,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    product,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.product_metadata_updated(product)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_METADATA_UPDATED,
        [any_webhook],
        product,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.product_variant_created(variant)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_VARIANT_CREATED,
        [any_webhook],
        variant,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.product_variant_updated(variant)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        [any_webhook],
        variant,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.product_variant_deleted(variant)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_VARIANT_DELETED,
        [any_webhook],
        variant,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    variant,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.product_variant_metadata_updated(variant)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED,
        [any_webhook],
        variant,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.product_variant_out_of_stock(variant)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK,
        [any_webhook],
        variant,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert callable(mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"])
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.product_variant_back_in_stock(variant)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK,
        [any_webhook],
        variant,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert callable(mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"])
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@freeze_time("2014-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async_for_multiple_objects")
def test_product_variant_stocks_updated(
    mocked_webhook_trigger_for_multiple_objects,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    variant_with_many_stocks,
):
    stock = variant_with_many_stocks.stocks.first()
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.product_variant_stocks_updated([stock])

    mocked_webhook_trigger_for_multiple_objects.assert_called_once_with(
        WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED,
        [any_webhook],
        webhook_payloads_data=[
            WebhookPayloadData(
                subscribable_object=stock, legacy_data_generator=ANY, data=None
            )
        ],
        requestor=None,
    )

    assert callable(
        mocked_webhook_trigger_for_multiple_objects.call_args.kwargs[
            "webhook_payloads_data"
        ][0].legacy_data_generator
    )
    assert isinstance(
        mocked_webhook_trigger_for_multiple_objects.call_args.kwargs[
            "webhook_payloads_data"
        ][0].legacy_data_generator,
        partial,
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.order_updated(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_UPDATED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.order_cancelled(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_CANCELLED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_expired(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.order_expired(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_EXPIRED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_order_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order_with_lines,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.order_metadata_updated(order_with_lines)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.ORDER_METADATA_UPDATED,
        [any_webhook],
        order_with_lines,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    manager.checkout_created(checkout_with_items)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.CHECKOUT_CREATED,
        [any_webhook],
        checkout_with_items,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


def test_checkout_payload_includes_promotions(
    checkout_with_item, catalogue_promotion_without_rules
):
    # given
    checkout = checkout_with_item
    checkout_lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    variant = checkout_lines[0].variant
    channel_listing = variant.channel_listings.first()

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel_listing.channel)

    channel_listing.discounted_price_amount = (
        channel_listing.price_amount - reward_value
    )
    channel_listing.save(update_fields=["discounted_price_amount"])

    listing_promotion_rule = channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel_listing.channel.currency_code,
    )

    checkout_lines[0].rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines
    )

    variant_price_with_sale = variant.get_price(
        channel_listing=channel_listing,
    )
    variant_price_without_sale = variant.get_base_price(
        channel_listing=channel_listing,
    )

    # when
    data = json.loads(generate_checkout_payload(checkout))

    # then
    assert variant_price_without_sale > variant_price_with_sale
    assert Decimal(data[0]["lines"][0]["base_price"]) == variant_price_with_sale.amount


def test_checkout_payload_includes_order_promotion_discount(
    checkout_with_item, catalogue_promotion_without_rules
):
    # given
    checkout = checkout_with_item
    checkout_lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    variant = checkout_lines[0].variant
    channel_listing = variant.channel_listings.first()

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        name="Fixed promotion rule",
        order_predicate={
            "discountedObjectPredicate": {
                "baseTotalPrice": {
                    "range": {
                        "gte": 20,
                    }
                }
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel_listing.channel)

    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines
    )
    checkout.save(
        update_fields=[
            "discount_amount",
            "discount_name",
            "translated_discount_name",
        ]
    )

    # when
    data = json.loads(generate_checkout_payload(checkout))

    # then
    variant_price = variant.get_price(
        channel_listing=channel_listing,
    )
    assert Decimal(data[0]["discount_amount"]) == reward_value
    assert data[0]["discount_name"] == checkout.discount_name
    assert Decimal(data[0]["lines"][0]["base_price"]) == variant_price.amount


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
    manager = get_plugins_manager(allow_replica=False)
    manager.checkout_updated(checkout_with_items)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.CHECKOUT_UPDATED,
        [any_webhook],
        checkout_with_items,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@freeze_time("2014-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_checkout_fully_paid(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    checkout_with_items,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.checkout_fully_paid(checkout_with_items)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.CHECKOUT_FULLY_PAID,
        [any_webhook],
        checkout_with_items,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_checkout_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    checkout_with_items,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.checkout_metadata_updated(checkout_with_items)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED,
        [any_webhook],
        checkout_with_items,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_created(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, page
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.page_created(page)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PAGE_CREATED,
        [any_webhook],
        page,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_updated(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, page
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.page_updated(page)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PAGE_UPDATED,
        [any_webhook],
        page,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_deleted(
    mocked_webhook_trigger, mocked_get_webhooks_for_event, any_webhook, settings, page
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    page_id = page.id
    page.delete()
    page.id = page_id
    manager.page_deleted(page)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PAGE_DELETED,
        [any_webhook],
        page,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    invoice = fulfilled_order.invoices.first()
    manager.invoice_request(fulfilled_order, invoice, invoice.number)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.INVOICE_REQUESTED,
        [any_webhook],
        invoice,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    invoice = fulfilled_order.invoices.first()
    manager.invoice_delete(invoice)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.INVOICE_DELETED,
        [any_webhook],
        invoice,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


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
    manager = get_plugins_manager(allow_replica=False)
    invoice = fulfilled_order.invoices.first()
    manager.invoice_sent(invoice, fulfilled_order.user.email)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.INVOICE_SENT,
        [any_webhook],
        invoice,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@freeze_time("2020-03-18 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_fulfillment_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    fulfillment,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.fulfillment_metadata_updated(fulfillment)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.FULFILLMENT_METADATA_UPDATED,
        [any_webhook],
        fulfillment,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_gift_card_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    gift_card,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.gift_card_metadata_updated(gift_card)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED,
        [any_webhook],
        gift_card,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    voucher,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.voucher_metadata_updated(voucher)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.VOUCHER_METADATA_UPDATED,
        [any_webhook],
        voucher,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shop_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
):
    site_settings = SiteSettings.objects.first()
    assert site_settings
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.shop_metadata_updated(site_settings)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.SHOP_METADATA_UPDATED,
        [any_webhook],
        site_settings,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shipping_zone_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    shipping_zone,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.shipping_zone_metadata_updated(shipping_zone)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.SHIPPING_ZONE_METADATA_UPDATED,
        [any_webhook],
        shipping_zone,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_warehouse_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    warehouse,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.warehouse_metadata_updated(warehouse)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED,
        [any_webhook],
        warehouse,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_transaction_item_metadata_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    transaction_item_created_by_app,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.transaction_item_metadata_updated(transaction_item_created_by_app)

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED,
        [any_webhook],
        transaction_item_created_by_app,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
        queue=None,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
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
    manager = get_plugins_manager(True, lambda: customer_user)
    timestamp = datetime.datetime(2020, 3, 18, 12, 0, tzinfo=datetime.UTC).isoformat()

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
        json.dumps(data),
        WebhookEventAsyncType.NOTIFY_USER,
        [any_webhook],
        allow_replica=True,
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
        "saleor.webhook.transport.utils.boto3.client",
        mocked_client_constructor,
    )

    webhook.app.permissions.add(permission_manage_orders)

    webhook.target_url = "testy"
    webhook.save()
    expected_data = serialize("json", [order_with_lines])
    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )
    delivery = EventDelivery.objects.first()
    send_webhook_request_async(delivery.id)
    attempt = EventDeliveryAttempt.objects.first()
    payload = EventPayload.objects.first()

    assert delivery
    assert attempt
    assert delivery.webhook == webhook
    assert delivery.event_type == WebhookEventAsyncType.ORDER_CREATED
    assert attempt.response == "Unknown webhook scheme: ''"
    assert delivery.status == "failed"
    assert attempt.task_id == ANY
    assert attempt.duration == ANY
    assert payload.get_payload() == expected_data
    assert payload.payload_file


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_created(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    promotion_converted_from_sale,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    promotion = promotion_converted_from_sale
    predicate = promotion.rules.first().catalogue_predicate
    promotion_catalogue_info = convert_migrated_sale_predicate_to_catalogue_info(
        predicate
    )

    manager.sale_created(promotion, current_catalogue=promotion_catalogue_info)
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.SALE_CREATED,
        [any_webhook],
        promotion,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_updated(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    promotion_converted_from_sale,
    product_list,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    promotion = promotion_converted_from_sale
    rule = promotion.rules.first()
    predicate = promotion.rules.first().catalogue_predicate
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]
    predicate = {"variantPredicate": {"ids": [product_ids]}}
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    manager.sale_updated(
        promotion,
        previous_catalogue=previous_catalogue,
        current_catalogue=current_catalogue,
    )
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.SALE_UPDATED,
        [any_webhook],
        promotion,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_deleted(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    promotion_converted_from_sale,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    promotion = promotion_converted_from_sale
    predicate = promotion.rules.first().catalogue_predicate
    catalogue_info = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    manager.sale_deleted(promotion, previous_catalogue=catalogue_info)
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.SALE_DELETED,
        [any_webhook],
        promotion,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@freeze_time("2020-10-10 10:10")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_toggle(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    promotion_converted_from_sale,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    promotion = promotion_converted_from_sale
    predicate = promotion.rules.first().catalogue_predicate
    catalogue_info = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    # when
    manager.sale_toggle(promotion, catalogue=catalogue_info)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.SALE_TOGGLE,
        [any_webhook],
        promotion,
        None,
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.send_webhook_request_async.delay")
def test_event_delivery_retry(mocked_webhook_send, event_delivery, settings):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.event_delivery_retry(event_delivery)

    # then
    mocked_webhook_send.assert_called_once_with(event_delivery.pk)


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.observability.report_event_delivery_attempt"
)
@mock.patch("saleor.webhook.transport.asynchronous.transport.clear_successful_delivery")
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async(
    mocked_send_response,
    mocked_clear_delivery,
    mocked_observability,
    event_delivery,
    webhook_response,
):
    mocked_send_response.return_value = webhook_response
    send_webhook_request_async(event_delivery.pk)

    mocked_send_response.assert_called_once_with(
        event_delivery.webhook.target_url,
        "mirumee.com",
        event_delivery.webhook.secret_key,
        event_delivery.event_type,
        event_delivery.payload.get_payload().encode("utf-8"),
        event_delivery.webhook.custom_headers,
    )
    mocked_clear_delivery.assert_called_once_with(event_delivery)
    attempt = EventDeliveryAttempt.objects.filter(delivery=event_delivery).first()
    delivery = EventDelivery.objects.get(id=event_delivery.pk)

    assert attempt
    assert delivery
    assert attempt.status == EventDeliveryStatus.SUCCESS
    assert attempt.response == webhook_response.content
    assert attempt.response_headers == json.dumps(webhook_response.response_headers)
    assert attempt.response_status_code == webhook_response.response_status_code
    assert attempt.request_headers == json.dumps(webhook_response.request_headers)
    assert attempt.duration == webhook_response.duration
    assert delivery.status == EventDeliveryStatus.SUCCESS
    mocked_observability.assert_called_once_with(attempt)


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async_with_custom_headers(
    mocked_send_response,
    event_delivery,
    webhook_response,
):
    # given
    mocked_send_response.return_value = webhook_response
    custom_headers = {"X-Key": "Value", "Authorization-Key": "Value"}
    event_delivery.webhook.custom_headers = custom_headers
    event_delivery.webhook.save(update_fields=["custom_headers"])

    # when
    send_webhook_request_async(event_delivery.pk)

    # then
    mocked_send_response.assert_called_once()
    assert custom_headers in mocked_send_response.call_args[0]


@mock.patch("saleor.webhook.observability.utils.report_event_delivery_attempt")
@mock.patch("saleor.webhook.transport.utils.clear_successful_delivery")
def test_send_webhook_request_async_when_webhook_is_disabled(
    mocked_clear_delivery, mocked_observability, event_delivery
):
    # given
    event_delivery.webhook.is_active = False
    event_delivery.webhook.save(update_fields=["is_active"])

    # when
    send_webhook_request_async(event_delivery.pk)
    event_delivery.refresh_from_db()

    # then
    assert not mocked_clear_delivery.called
    assert not mocked_observability.called
    assert event_delivery.status == EventDeliveryStatus.FAILED


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_transaction_request")
def test_transaction_charge_requested(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order,
    channel_USD,
    app,
):
    # given
    any_webhook.app = app
    any_webhook.save()

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app_identifier=app.identifier,
        app=app,
    )
    event = transaction.events.create(type=TransactionEventType.CHARGE_REQUEST)
    action_value = Decimal("5.00")
    transaction_action_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.CHARGE,
        action_value=action_value,
        event=event,
        transaction_app_owner=app,
    )

    # when
    manager.transaction_charge_requested(
        transaction_action_data, channel_slug=channel_USD.slug
    )

    # then
    mocked_webhook_trigger.assert_called_once_with(
        transaction_action_data,
        WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
        None,
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_transaction_request")
def test_transaction_refund_requested(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order,
    channel_USD,
    app,
):
    # given
    any_webhook.app = app
    any_webhook.save()

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=[
            "refund",
        ],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app_identifier=app.identifier,
        app=app,
    )
    event = transaction.events.create(type=TransactionEventType.REFUND_REQUEST)
    action_value = Decimal("5.00")
    transaction_action_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.REFUND,
        action_value=action_value,
        event=event,
        transaction_app_owner=app,
    )

    # when
    manager.transaction_refund_requested(
        transaction_action_data, channel_slug=channel_USD.slug
    )

    # then
    mocked_webhook_trigger.assert_called_once_with(
        transaction_action_data,
        WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        None,
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_transaction_request")
def test_transaction_refund_requested_missing_app_owner_updated_refundable_for_checkout(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    checkout,
    channel_USD,
    app,
):
    # given
    checkout.automatically_refundable = True
    checkout.save()
    any_webhook.app = app
    any_webhook.save()

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=[
            "refund",
        ],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal("10"),
        app_identifier=app.identifier,
        app=app,
    )
    event = transaction.events.create(type=TransactionEventType.REFUND_REQUEST)
    action_value = Decimal("5.00")
    transaction_action_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.REFUND,
        action_value=action_value,
        event=event,
        transaction_app_owner=None,
    )

    # when
    manager.transaction_refund_requested(
        transaction_action_data, channel_slug=channel_USD.slug
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_transaction_request")
def test_transaction_cancel_requested_missing_app_owner_updated_refundable_for_checkout(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    checkout,
    channel_USD,
    app,
):
    # given
    checkout.automatically_refundable = True
    checkout.save()
    any_webhook.app = app
    any_webhook.save()

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=[
            "refund",
        ],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal("10"),
        app_identifier=app.identifier,
        app=app,
    )
    event = transaction.events.create(type=TransactionEventType.CANCEL_REQUEST)
    action_value = Decimal("5.00")
    transaction_action_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.CANCEL,
        action_value=action_value,
        event=event,
        transaction_app_owner=None,
    )

    # when
    manager.transaction_refund_requested(
        transaction_action_data, channel_slug=channel_USD.slug
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_transaction_request")
def test_transaction_cancelation_requested(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    settings,
    order,
    channel_USD,
    app,
):
    # given
    any_webhook.app = app
    any_webhook.save()

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=[
            "refund",
        ],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app_identifier=app.identifier,
        app=app,
    )
    event = transaction.events.create(type=TransactionEventType.CANCEL_REQUEST)
    action_value = Decimal("5.00")
    transaction_action_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.CANCEL,
        action_value=action_value,
        event=event,
        transaction_app_owner=app,
    )

    # when
    manager.transaction_cancelation_requested(
        transaction_action_data, channel_slug=channel_USD.slug
    )
    # then
    mocked_webhook_trigger.assert_called_once_with(
        transaction_action_data,
        WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED,
        None,
    )


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.observability.report_event_delivery_attempt"
)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async_when_delivery_attempt_failed(
    mocked_send_response,
    mocked_observability,
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
    mocked_observability.assert_called_once_with(attempt, None)


@mock.patch.object(HTTPSession, "request", side_effect=RequestException)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.observability.report_event_delivery_attempt"
)
def test_send_webhook_request_async_with_request_exception(
    mocked_observability, mocked_post, event_delivery, webhook_response_failed
):
    # given
    event_payload = event_delivery.payload
    data = event_payload.get_payload()
    webhook = event_delivery.webhook
    domain = Site.objects.get_current().domain
    message = data.encode("utf-8")
    signature = signature_for_payload(message, webhook.secret_key)
    expected_request_headers = generate_request_headers(
        event_delivery.event_type, domain, signature
    )
    # when
    with pytest.raises(CeleryTaskRetryError):
        send_webhook_request_async(event_delivery.pk)

    # then

    attempt = EventDeliveryAttempt.objects.filter(delivery=event_delivery).first()
    delivery = EventDelivery.objects.get(id=event_delivery.pk)
    assert attempt.status == EventDeliveryStatus.FAILED
    assert json.loads(attempt.request_headers) == expected_request_headers
    assert delivery.status == EventDeliveryStatus.PENDING
    mocked_observability.assert_called_once_with(attempt, None)


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.retry"
)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.observability.report_event_delivery_attempt"
)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async_when_max_retries_exceeded(
    mocked_send_response,
    mocked_observability,
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
    mocked_observability.assert_called_once_with(attempt)


def test_is_event_active(settings, webhook, permission_manage_orders):
    # given
    event = "invoice_request"
    expected_is_active = True
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook.app.permissions.add(permission_manage_orders)
    webhook.events.create(event_type=WebhookEventAsyncType.INVOICE_REQUESTED)

    manager = get_plugins_manager(allow_replica=False)

    # when
    is_active = manager.is_event_active_for_any_plugin(event)

    # then
    assert is_active == expected_is_active


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch("saleor.webhook.transport.synchronous.transport.get_webhooks_for_event")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_trigger_webhook_sync_with_subscription_within_mutation_use_default_db(
    mocked_generate_payload,
    mocked_get_webhooks_for_event,
    mocked_request,
    draft_order,
    app_api_client,
    permission_manage_orders,
    settings,
    subscription_calculate_taxes_for_order,
):
    # given
    webhook = subscription_calculate_taxes_for_order
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_get_webhooks_for_event.return_value = [webhook]
    variables = {
        "orderId": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": Decimal("50"),
        },
    }
    app_api_client.app.permissions.add(permission_manage_orders)

    # when
    app_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)

    # then
    mocked_generate_payload.assert_called_once()
    assert not mocked_generate_payload.call_args[1]["request"].allow_replica


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async"
)
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.generate_payload_from_subscription"
)
def test_trigger_webhook_async_with_subscription_use_main_db(
    mocked_generate_payload,
    mocked_get_webhooks_for_event,
    mocked_request,
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
    subscription_product_created_webhook,
    settings,
):
    # given
    webhook = subscription_product_created_webhook
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_get_webhooks_for_event.return_value = [webhook]

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
        }
    }

    # when
    staff_api_client.post_graphql(
        CREATE_PRODUCT_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    mocked_generate_payload.assert_called_once()
    assert not mocked_generate_payload.call_args[1]["request"].allow_replica
