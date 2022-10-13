from typing import Type

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
from ..utils import get_webhooks_for_event


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
    "error,event_type",
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
    error: Type[TruncationError], event_type: ObservabilityEventTypes
):
    operation, bytes_limit, payload_size = "operation_name", 100, 102
    kwargs = dict(extra_kwarg_a="a", extra_kwarg_b="b")
    err = error(operation, bytes_limit, payload_size, **kwargs)
    assert str(err)
    assert err.extra == {
        **{
            "observability_event_type": event_type,
            "operation": operation,
            "bytes_limit": bytes_limit,
            "payload_size": payload_size,
        },
        **kwargs,
    }
