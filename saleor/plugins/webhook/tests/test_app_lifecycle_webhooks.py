"""End-to-end tests for app lifecycle webhook self-receive.

Confirms an app without MANAGE_APPS permission receives its own
APP_INSTALLED, APP_UPDATED, APP_DELETED, APP_STATUS_CHANGED events,
and that the delivery-time gate keeps lifecycle deliveries when the
receiving app is inactive (soft-deleted or deactivated).
"""

import json
from unittest import mock

import graphene
import pytest
from django.utils import timezone

from ....app.models import App
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook
from ....webhook.transport.utils import get_multiple_deliveries_for_webhooks
from ...manager import get_plugins_manager

APP_STATUS_CHANGED_SUBSCRIPTION = """
subscription {
  event {
    ... on AppStatusChanged {
      app {
        id
        isActive
      }
    }
  }
}
"""


@pytest.fixture
def app_with_lifecycle_webhook(db, settings):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    def factory(event_type, *, is_active=True, removed_at=None, subscription_query=""):
        app = App.objects.create(name="Self-receive app", is_active=is_active)
        if removed_at:
            app.removed_at = removed_at
            app.save(update_fields=["removed_at"])
        webhook = Webhook.objects.create(
            name="lifecycle",
            app=app,
            target_url="http://example.com/webhook",
            is_active=True,
            subscription_query=subscription_query,
        )
        webhook.events.create(event_type=event_type)
        return app, webhook

    return factory


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_app_receives_own_app_installed_without_manage_apps(
    mocked_trigger, app_with_lifecycle_webhook
):
    # given
    app, webhook = app_with_lifecycle_webhook(WebhookEventAsyncType.APP_INSTALLED)
    assert not app.permissions.exists()

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_installed(app)

    # then
    mocked_trigger.assert_called_once()
    delivered_webhooks = mocked_trigger.call_args.args[2]
    assert webhook in list(delivered_webhooks)


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_app_receives_own_app_updated_without_manage_apps(
    mocked_trigger, app_with_lifecycle_webhook
):
    # given
    app, webhook = app_with_lifecycle_webhook(WebhookEventAsyncType.APP_UPDATED)
    assert not app.permissions.exists()

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_updated(app)

    # then
    mocked_trigger.assert_called_once()
    delivered_webhooks = mocked_trigger.call_args.args[2]
    assert webhook in list(delivered_webhooks)


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_app_receives_own_app_deleted_without_manage_apps(
    mocked_trigger, app_with_lifecycle_webhook
):
    """Verify self-receive for the soft-deleted app.

    The affected app is soft-deleted (is_active=False, removed_at set)
    at dispatch time, yet must still receive APP_DELETED.
    """
    # given
    app, webhook = app_with_lifecycle_webhook(
        WebhookEventAsyncType.APP_DELETED,
        is_active=False,
        removed_at=timezone.now(),
    )
    assert not app.permissions.exists()

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_deleted(app)

    # then
    mocked_trigger.assert_called_once()
    delivered_webhooks = mocked_trigger.call_args.args[2]
    assert webhook in list(delivered_webhooks)


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_app_receives_own_app_status_changed_on_deactivate(
    mocked_trigger, app_with_lifecycle_webhook
):
    """Verify self-receive for the deactivated app.

    A deactivated app (is_active=False) must still receive its own
    APP_STATUS_CHANGED webhook.
    """
    # given
    app, webhook = app_with_lifecycle_webhook(
        WebhookEventAsyncType.APP_STATUS_CHANGED, is_active=False
    )
    assert not app.permissions.exists()

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_status_changed(app)

    # then
    mocked_trigger.assert_called_once()
    delivered_webhooks = mocked_trigger.call_args.args[2]
    assert webhook in list(delivered_webhooks)


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_unrelated_app_without_manage_apps_does_not_receive_lifecycle_event(
    mocked_trigger, app_with_lifecycle_webhook
):
    """An app subscribed to APP_DELETED must not receive events about other apps."""
    # given
    affected_app = App.objects.create(name="Target", is_active=True)
    app_with_lifecycle_webhook(WebhookEventAsyncType.APP_DELETED)

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_deleted(affected_app)

    # then
    assert not mocked_trigger.called


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_admin_app_with_manage_apps_does_not_receive_events_about_other_apps(
    mocked_trigger, app_with_lifecycle_webhook, permission_manage_apps
):
    """App lifecycle events are self-only — MANAGE_APPS does not grant visibility."""
    # given
    affected_app = App.objects.create(name="Target", is_active=True)
    admin_app, _ = app_with_lifecycle_webhook(WebhookEventAsyncType.APP_DELETED)
    admin_app.permissions.add(permission_manage_apps)

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_deleted(affected_app)

    # then
    assert not mocked_trigger.called


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_app_deleted_delivery_survives_worker_active_check(
    _mocked_apply_async, app_with_lifecycle_webhook
):
    """APP_DELETED on a soft-deleted app passes the delivery-time gate."""
    # given
    app, webhook = app_with_lifecycle_webhook(
        WebhookEventAsyncType.APP_DELETED,
        is_active=False,
        removed_at=timezone.now(),
    )

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_deleted(app)
    delivery = EventDelivery.objects.get(webhook=webhook)
    active, inactive = get_multiple_deliveries_for_webhooks([delivery.pk])

    # then
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.pk in active
    assert delivery.pk not in inactive
    delivery.refresh_from_db()
    assert delivery.status == EventDeliveryStatus.PENDING


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_app_status_changed_delivery_survives_worker_active_check(
    _mocked_apply_async, app_with_lifecycle_webhook
):
    """APP_STATUS_CHANGED on a deactivated app passes the delivery-time gate."""
    # given
    app, webhook = app_with_lifecycle_webhook(
        WebhookEventAsyncType.APP_STATUS_CHANGED, is_active=False
    )

    # when
    manager = get_plugins_manager(allow_replica=False)
    manager.app_status_changed(app)
    delivery = EventDelivery.objects.get(webhook=webhook)
    active, _ = get_multiple_deliveries_for_webhooks([delivery.pk])

    # then
    assert delivery.pk in active
    delivery.refresh_from_db()
    assert delivery.status == EventDeliveryStatus.PENDING


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_app_status_changed_subscription_payload_snapshots_state_per_event(
    _mocked_apply_async, app_with_lifecycle_webhook
):
    """Subscription payload reflects app.is_active at dispatch time.

    With delivery deferred (apply_async mocked), back-to-back deactivate
    then activate must produce two PENDING deliveries whose subscription
    payloads carry isActive=False and isActive=True respectively. This
    proves payloads are snapshotted at event time and survive the queue
    delay independent of the app's current state.
    """
    # given
    app, webhook = app_with_lifecycle_webhook(
        WebhookEventAsyncType.APP_STATUS_CHANGED,
        is_active=True,
        subscription_query=APP_STATUS_CHANGED_SUBSCRIPTION,
    )
    app_global_id = graphene.Node.to_global_id("App", app.id)
    manager = get_plugins_manager(allow_replica=False)

    # when
    app.is_active = False
    app.save(update_fields=["is_active"])
    manager.app_status_changed(app)

    app.is_active = True
    app.save(update_fields=["is_active"])
    manager.app_status_changed(app)

    # then
    deliveries = list(EventDelivery.objects.filter(webhook=webhook).order_by("pk"))
    assert len(deliveries) == 2
    assert all(d.status == EventDeliveryStatus.PENDING for d in deliveries)

    deactivate_payload = json.loads(deliveries[0].payload.get_payload())
    activate_payload = json.loads(deliveries[1].payload.get_payload())

    assert deactivate_payload == {"app": {"id": app_global_id, "isActive": False}}
    assert activate_payload == {"app": {"id": app_global_id, "isActive": True}}
