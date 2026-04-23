import json
from unittest.mock import Mock, patch

import graphene

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


@patch("saleor.app.actions.trigger_webhook_sync_promise")
@patch("saleor.app.actions.get_webhooks_for_app_lifecycle_event")
def test_delete_app_force_sync_bypasses_manager_and_calls_trigger_webhook_sync(
    mocked_get_webhooks, mocked_trigger_sync, app
):
    # given
    manager = Mock()
    webhook_a = Mock()
    webhook_b = Mock()
    mocked_get_webhooks.return_value = [webhook_a, webhook_b]

    # when
    delete_app(app, manager, force_sync=True)

    # then
    app_from_db = App.objects.get(pk=app.pk)
    assert app_from_db.removed_at is not None
    assert app_from_db.is_active is False
    manager.app_deleted.assert_not_called()

    assert mocked_trigger_sync.call_count == 2
    expected_payload_fragment = {
        "id": graphene.Node.to_global_id("App", app.id),
        "is_active": False,
        "name": app.name,
    }
    for webhook, webhook_call in zip(
        [webhook_a, webhook_b], mocked_trigger_sync.call_args_list, strict=True
    ):
        kwargs = webhook_call.kwargs
        assert kwargs["event_type"] == "app_deleted"
        assert kwargs["webhook"] is webhook
        assert kwargs["allow_replica"] is False
        assert kwargs["subscribable_object"] is app
        payload = json.loads(kwargs["static_payload"])
        assert payload["id"] == expected_payload_fragment["id"]
        assert payload["is_active"] == expected_payload_fragment["is_active"]
        assert payload["name"] == expected_payload_fragment["name"]
        assert "meta" in payload


@patch("saleor.app.actions.trigger_webhook_sync_promise")
@patch("saleor.app.actions.get_webhooks_for_app_lifecycle_event")
def test_delete_app_force_sync_with_no_webhooks_does_not_trigger(
    mocked_get_webhooks, mocked_trigger_sync, app
):
    # given
    manager = Mock()
    mocked_get_webhooks.return_value = []

    # when
    delete_app(app, manager, force_sync=True)

    # then
    app_from_db = App.objects.get(pk=app.pk)
    assert app_from_db.removed_at is not None
    assert app_from_db.is_active is False
    manager.app_deleted.assert_not_called()
    mocked_trigger_sync.assert_not_called()
