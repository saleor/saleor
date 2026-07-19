import json
from unittest.mock import Mock, patch

import graphene

from ...core.models import EventDelivery, EventPayload
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.models import Webhook
from ..actions import delete_app
from ..models import App


def test_delete_app_soft_deletes_and_calls_app_deleted(
    app, django_capture_on_commit_callbacks
):
    # given
    manager = Mock()
    assert app.removed_at is None
    assert app.is_active is True

    # when
    with django_capture_on_commit_callbacks(execute=True):
        delete_app(app, manager)

    # then
    app_from_db = App.objects.get(pk=app.pk)
    assert app_from_db.removed_at is not None
    assert app_from_db.is_active is False
    manager.app_deleted.assert_called_once_with(app)


@patch("saleor.app.actions.send_webhook_request_async.apply")
def test_delete_app_force_sync_renders_subscription_inline(mocked_apply, app):
    # given
    manager = Mock()
    subscription_query = """
        subscription { event { ... on AppDeleted { app { id isActive name } } } }
    """
    webhook = Webhook.objects.create(
        name="subscription",
        app=app,
        target_url="http://example.com/sub",
        is_active=True,
        subscription_query=subscription_query,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.APP_DELETED)

    # when
    delete_app(app, manager, force_sync=True)

    # then
    delivery = EventDelivery.objects.get(webhook=webhook)
    assert delivery.event_type == WebhookEventAsyncType.APP_DELETED
    payload = json.loads(delivery.payload.get_payload())
    assert payload == {
        "app": {
            "id": graphene.Node.to_global_id("App", app.id),
            "isActive": False,
            "name": app.name,
        }
    }

    mocked_apply.assert_called_once()
    call_kwargs = mocked_apply.call_args.kwargs["kwargs"]
    assert call_kwargs["event_delivery_id"] == delivery.pk
    assert "telemetry_context" in call_kwargs


@patch("saleor.app.actions.send_webhook_request_async.apply")
def test_delete_app_force_sync_skips_legacy_webhooks_without_subscription(
    mocked_apply, app
):
    # Legacy non-subscription webhooks are not supported. Effectively these webhooks
    # exist in the code, but app installation enforces subscription, so we don't have
    # to support them.
    # static_payload should be eventually removed from the codebase

    # given
    manager = Mock()
    legacy_webhook = Webhook.objects.create(
        name="legacy",
        app=app,
        target_url="http://example.com/legacy",
        is_active=True,
    )
    legacy_webhook.events.create(event_type=WebhookEventAsyncType.APP_DELETED)

    # when
    delete_app(app, manager, force_sync=True)

    # then
    assert not EventDelivery.objects.filter(webhook=legacy_webhook).exists()
    assert not EventPayload.objects.exists()
    mocked_apply.assert_not_called()


@patch("saleor.app.actions.send_webhook_request_async.apply")
def test_delete_app_force_sync_with_no_webhooks_does_not_create_deliveries(
    mocked_apply, app
):
    # given
    manager = Mock()
    assert not app.webhooks.exists()

    # when
    delete_app(app, manager, force_sync=True)

    # then
    app_from_db = App.objects.get(pk=app.pk)
    assert app_from_db.removed_at is not None
    assert app_from_db.is_active is False
    manager.app_deleted.assert_not_called()
    assert not EventDelivery.objects.exists()
    assert not EventPayload.objects.exists()
    mocked_apply.assert_not_called()
