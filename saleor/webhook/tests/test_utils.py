import pytest

from ...app.models import App
from ..event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..models import Webhook
from ..observability.exceptions import (
    ApiCallTruncationError,
    EventDeliveryAttemptTruncationError,
    TruncationError,
)
from ..observability.payload_schema import ObservabilityEventTypes
from ..transport.utils import (
    generate_cache_key_for_webhook,
)
from ..utils import get_webhooks_for_event, get_webhooks_for_multiple_events


@pytest.fixture
def sync_type():
    return WebhookEventSyncType.PAYMENT_AUTHORIZE


@pytest.fixture
def async_type():
    return WebhookEventAsyncType.ORDER_CREATED


@pytest.fixture
def sync_webhook(db, permission_manage_payments, sync_type):
    app = App.objects.create(name="Sync App", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(name="sync-webhook", app=app)
    webhook.events.create(event_type=sync_type, webhook=webhook)
    return webhook


@pytest.fixture
def async_app_factory(db, permission_manage_orders, async_type):
    def create_app(active_app=True, active_webhook=True, any_webhook=False):
        app = App.objects.create(name="Async App", is_active=active_app)
        app.tokens.create(name="Default")
        app.permissions.add(permission_manage_orders)
        webhook = Webhook.objects.create(
            name="async-webhook", app=app, is_active=active_webhook
        )
        event_type = WebhookEventAsyncType.ANY if any_webhook else async_type
        webhook.events.create(event_type=event_type, webhook=webhook)
        return app, webhook

    return create_app


def test_get_webhooks_for_event(sync_webhook, async_app_factory, async_type):
    _, async_webhook = async_app_factory()
    _, any_webhook = async_app_factory(any_webhook=True)

    webhooks = get_webhooks_for_event(async_type)

    assert set(webhooks) == {async_webhook, any_webhook}


def test_get_webhooks_for_event_when_app_webhook_inactive(
    sync_webhook, async_app_factory, async_type
):
    async_app_factory(active_app=False, active_webhook=True)
    async_app_factory(active_app=True, active_webhook=False)
    _, any_webhook = async_app_factory()

    webhooks = get_webhooks_for_event(async_type)

    assert set(webhooks) == {any_webhook}


def test_get_webhooks_for_event_when_webhooks_provided(async_app_factory, async_type):
    _, async_webhook_a = async_app_factory()
    _, async_webhook_b = async_app_factory(any_webhook=True)
    _, _ = async_app_factory()
    webhooks_ids = [async_webhook_a.id, async_webhook_b.id]

    webhooks = get_webhooks_for_event(
        async_type, Webhook.objects.filter(id__in=webhooks_ids)
    )

    assert set(webhooks) == {async_webhook_a, async_webhook_b}


def test_get_webhooks_for_event_when_app_has_no_permissions(
    async_app_factory, async_type
):
    _, async_webhook_a = async_app_factory()
    app, _ = async_app_factory(any_webhook=True)
    app.permissions.clear()

    webhooks = get_webhooks_for_event(async_type)

    assert set(webhooks) == {async_webhook_a}


def test_get_webhook_for_event_no_duplicates(async_app_factory, async_type):
    _, async_webhook = async_app_factory()
    async_webhook.events.create(event_type=WebhookEventAsyncType.ANY)

    webhooks = get_webhooks_for_event(async_type)

    assert webhooks.count() == 1


def test_get_webhook_for_event_not_returning_any_webhook_for_sync_event_types(
    sync_webhook, async_app_factory, sync_type, permission_manage_payments
):
    any_app, _ = async_app_factory(any_webhook=True)
    any_app.permissions.add(permission_manage_payments)

    webhooks = get_webhooks_for_event(sync_type)

    assert set(webhooks) == {sync_webhook}


@pytest.mark.parametrize(
    ("error", "event_type"),
    [
        (
            ApiCallTruncationError,
            ObservabilityEventTypes.API_CALL,
        ),
        (
            EventDeliveryAttemptTruncationError,
            ObservabilityEventTypes.EVENT_DELIVERY_ATTEMPT,
        ),
    ],
)
def test_truncation_error_extra_fields(
    error: type[TruncationError], event_type: ObservabilityEventTypes
):
    operation, bytes_limit, payload_size = "operation_name", 100, 102
    kwargs = {"extra_kwarg_a": "a", "extra_kwarg_b": "b"}
    err = error(operation, bytes_limit, payload_size, **kwargs)
    assert str(err)
    assert err.extra == {
        "observability_event_type": event_type,
        "operation": operation,
        "bytes_limit": bytes_limit,
        "payload_size": payload_size,
        **kwargs,
    }


def test_get_webhooks_for_multiple_events(
    async_app_factory, async_type, setup_checkout_webhooks, app, external_app
):
    # given
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_created_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    attribute_created_webhook = app.webhooks.create(
        name="Attribute webhook",
        target_url="http://127.0.0.1/test",
    )
    attribute_created_webhook.events.create(
        event_type=WebhookEventAsyncType.ATTRIBUTE_CREATED
    )
    second_attribute_created_webhook = app.webhooks.create(
        name="Second attribute webhook",
        target_url="http://127.0.0.1/test",
    )
    second_attribute_created_webhook.events.create(
        event_type=WebhookEventAsyncType.ATTRIBUTE_CREATED
    )

    disabled_webhook = app.webhooks.create(
        name="Attribute webhook", target_url="http://127.0.0.1/test", is_active=False
    )
    disabled_webhook.events.create(event_type=WebhookEventAsyncType.ATTRIBUTE_CREATED)

    not_active_app = external_app
    not_active_app.is_active = False
    not_active_app.save()

    not_active_webhook = not_active_app.webhooks.create(
        name="Attribute webhook",
        target_url="http://127.0.0.1/test",
    )
    not_active_webhook.events.create(event_type=WebhookEventAsyncType.ATTRIBUTE_CREATED)

    # when
    webhook_map = get_webhooks_for_multiple_events(
        [
            WebhookEventAsyncType.CHECKOUT_CREATED,
            WebhookEventAsyncType.ATTRIBUTE_CREATED,
            WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
            WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
            WebhookEventAsyncType.ORDER_CREATED,
        ]
    )

    # then
    assert dict(webhook_map) == {
        WebhookEventAsyncType.ANY: set(),
        WebhookEventAsyncType.ORDER_CREATED: set(),
        WebhookEventAsyncType.CHECKOUT_CREATED: {checkout_created_webhook},
        WebhookEventAsyncType.ATTRIBUTE_CREATED: {
            attribute_created_webhook,
            second_attribute_created_webhook,
        },
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES: {tax_webhook},
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT: {shipping_webhook},
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS: {
            shipping_filter_webhook
        },
    }


def test_different_target_urls_produce_different_cache_key(checkout_with_item):
    # given
    target_url_1 = "http://example.com/1"
    target_url_2 = "http://example.com/2"

    payload = {"field": "1", "field2": "2"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload,
        target_url_1,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload,
        target_url_2,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )

    # then
    assert cache_key_1 != cache_key_2


def test_different_payload_produce_different_cache_key(checkout_with_item):
    # given
    target_url = "http://example.com/1"

    payload_1 = {"field": "1", "field2": "2"}
    payload_2 = {"field": "1", "field2": "3"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload_1,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload_2,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )

    # then
    assert cache_key_1 != cache_key_2


def test_different_event_produce_different_cache_key(checkout_with_item):
    # given
    target_url = "http://example.com/1"

    payload = {"field": "1", "field2": "2"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload, target_url, WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, 1
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload, target_url, WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS, 1
    )

    # then
    assert cache_key_1 != cache_key_2


def test_different_app_produce_different_cache_key():
    # given
    target_url = "http://example.com/1"
    first_app_id = 1
    second_app_id = 2
    payload = {"field": "1", "field2": "2"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        first_app_id,
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        second_app_id,
    )

    # then
    assert cache_key_1 != cache_key_2
