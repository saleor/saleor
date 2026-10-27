import json
from io import StringIO
from unittest.mock import ANY, Mock, call, patch

import graphene
import pytest
from django.core.management import CommandError, call_command
from django.forms import ValidationError
from django.utils import timezone
from requests_hardened import HTTPSession

from ... import schema_version
from ...core import JobStatus
from ...core.models import EventDelivery
from ...permission.enums import AppPermission, get_permissions
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.models import Webhook
from ..models import App, AppInstallation
from ..types import AppType


@pytest.mark.vcr
def test_creates_app_from_manifest():
    manifest_url = "http://otherapp:3000/manifest"
    call_command("install_app", manifest_url)

    app = App.objects.get()

    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert app.is_installed
    assert not app.is_active
    assert app.uuid is not None


@pytest.mark.vcr
def test_creates_app_from_manifest_activate_app():
    manifest_url = "http://otherapp:3000/manifest"
    call_command("install_app", manifest_url, activate=True)

    app = App.objects.get()

    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert app.is_installed
    assert app.is_active


@pytest.mark.vcr
def test_creates_app_from_manifest_app_has_all_required_permissions():
    manifest_url = "http://localhost:3000/manifest"
    permission_list = ["account.manage_users", "order.manage_orders"]
    expected_permission = get_permissions(permission_list)
    call_command("install_app", manifest_url)

    app = App.objects.get()
    assert set(app.permissions.all()) == set(expected_permission)


def test_creates_app_from_manifest_sends_token_when_target_url_provided(
    monkeypatch, app_manifest
):
    # given
    mocked_get = Mock(return_value=Mock())
    mocked_get.return_value.json = Mock(return_value=app_manifest)

    mocked_post = Mock(return_value=Mock())
    mocked_post.return_value.status_code = 200

    def _side_effect(_self, method, *args, **kwargs):
        if method == "GET":
            func = mocked_get
        elif method == "POST":
            func = mocked_post
        else:
            raise NotImplementedError("Method not implemented", method)
        return func(method, *args, **kwargs)

    monkeypatch.setattr(HTTPSession, "request", _side_effect)
    manifest_url = "http://localhost:3000/manifest"

    # when
    call_command("install_app", manifest_url)

    # then
    get_call = call(
        "GET",
        manifest_url,
        headers={"Saleor-Schema-Version": schema_version},
        timeout=ANY,
        allow_redirects=False,
    )
    mocked_get.assert_has_calls([get_call, get_call])
    mocked_post.assert_called_once_with(
        "POST",
        app_manifest["tokenTargetUrl"],
        headers={
            "Content-Type": "application/json",
            # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
            "X-Saleor-Domain": "example.com",
            "Saleor-Domain": "example.com",
            "Saleor-Api-Url": "https://example.com/graphql/",
            "Saleor-Schema-Version": schema_version,
        },
        json={"auth_token": ANY},
        allow_redirects=False,
    )


def test_creates_app_from_manifest_skips_sending_token_when_target_url_not_provided(
    monkeypatch, app_manifest
):
    # given
    app_manifest.pop("tokenTargetUrl")

    mocked_get = Mock(return_value=Mock())
    mocked_get.return_value.json = Mock(return_value=app_manifest)

    mocked_post = Mock(return_value=Mock())
    mocked_post.return_value.status_code = 200

    def _side_effect(_self, method, *args, **kwargs):
        if method == "GET":
            func = mocked_get
        elif method == "POST":
            func = mocked_post
        else:
            raise NotImplementedError("Method not implemented", method)
        return func(method, *args, **kwargs)

    monkeypatch.setattr(HTTPSession, "request", _side_effect)
    manifest_url = "http://localhost:3000/manifest"

    # when
    call_command("install_app", manifest_url)

    # then
    app = App.objects.get()
    get_call = call(
        "GET",
        manifest_url,
        headers={"Saleor-Schema-Version": schema_version},
        timeout=ANY,
        allow_redirects=False,
    )
    mocked_get.assert_has_calls([get_call, get_call])
    assert not mocked_post.called
    assert app.tokens.count() == 0


@pytest.mark.vcr
def test_creates_app_from_manifest_installation_failed():
    manifest_url = "http://localhost:3000/manifest-wrong"

    with pytest.raises(ValidationError, match="Invalid target url."):
        call_command("install_app", manifest_url)

    app_job = AppInstallation.objects.get()
    assert app_job.status == JobStatus.FAILED
    assert app_job.uuid is not None


@pytest.fixture
def installed_app():
    app = App.objects.create(
        name="Installed App",
        identifier="app.already.installed",
        is_active=True,
        is_installed=True,
        manifest_url="http://otherapp:3000/manifest",
        type=AppType.THIRDPARTY,
    )
    manifest_data = {
        "name": app.name,
        "version": "1.0.0",
        "id": app.identifier,
        "tokenTargetUrl": "http://otherapp:3000/register",
    }
    with patch(
        "saleor.app.management.commands.install_app.fetch_manifest",
        return_value=manifest_data,
    ):
        with patch(
            "saleor.app.installation_utils.fetch_manifest", return_value=manifest_data
        ):
            yield app


def test_creates_app_from_manifest_fails_on_already_installed_app(installed_app):
    with pytest.raises(
        ValidationError,
        match="App with the same identifier is already installed",
    ):
        call_command("install_app", installed_app.manifest_url)


def test_creates_app_from_manifest_quiet_skips_already_installed_app(installed_app):
    call_command("install_app", installed_app.manifest_url, quiet=True)

    assert App.objects.all().count() == 1

    app = App.objects.get()
    assert app.pk == installed_app.pk


def test_creates_app_object():
    name = "Single App"
    permissions = ["MANAGE_USERS", "MANAGE_ORDERS"]
    call_command("create_app", name, permission=permissions)

    apps = App.objects.filter(name=name)
    assert len(apps) == 1

    app = apps[0]
    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert app.uuid is not None
    assert app.identifier == graphene.Node.to_global_id("App", app.id)


def test_app_has_all_required_permissions():
    name = "SA name"
    expected_permission = get_permissions(
        ["account.manage_users", "order.manage_orders"]
    )
    call_command("create_app", name, permission=["MANAGE_USERS", "MANAGE_ORDERS"])

    apps = App.objects.filter(name=name)
    assert len(apps) == 1
    app = apps[0]
    assert set(app.permissions.all()) == set(expected_permission)


def test_sends_data_to_target_url(monkeypatch):
    mocked_response = Mock()
    mocked_response.status_code = 200
    mocked_post = Mock(return_value=mocked_response)

    monkeypatch.setattr(HTTPSession, "request", mocked_post)

    name = "Single App"
    target_url = "https://ss.shop.com/register"
    permissions = ["MANAGE_USERS"]

    call_command("create_app", name, permission=permissions, target_url=target_url)

    mocked_post.assert_called_once_with(
        "POST",
        target_url,
        headers={
            # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
            "X-Saleor-Domain": "example.com",
            "Saleor-Domain": "example.com",
            "Saleor-Api-Url": "https://example.com/graphql/",
            "Saleor-Schema-Version": schema_version,
        },
        json={"auth_token": ANY},
        allow_redirects=False,
    )


def test_create_app_command_rejects_manage_apps_permission():
    # given - the create_app command must not be a backdoor for granting MANAGE_APPS
    name = "Privileged App"
    manage_apps = AppPermission.MANAGE_APPS.name

    # when / then
    with pytest.raises(CommandError, match=manage_apps):
        call_command("create_app", name, permission=[manage_apps])

    assert not App.objects.filter(name=name).exists()


def test_creates_app_with_identifier():
    # given
    name = "Single App"
    permissions = ["MANAGE_USERS", "MANAGE_ORDERS"]

    # when
    call_command("create_app", name, permission=permissions, identifier="test.test")

    # then
    apps = App.objects.filter(name=name)
    assert len(apps) == 1

    app = apps[0]
    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert app.uuid is not None
    assert app.identifier == "test.test"


APP_DELETE_ALL_COMMAND_MODULE = "saleor.app.management.commands.app_delete_all"


@pytest.fixture
def _patched_plugins_manager():
    with patch(
        f"{APP_DELETE_ALL_COMMAND_MODULE}.get_plugins_manager"
    ) as mocked_get_manager:
        mocked_manager = Mock()
        mocked_get_manager.return_value = mocked_manager
        yield mocked_manager


def test_app_delete_all_deletes_every_installed_app(db):
    # given
    app_a = App.objects.create(name="App A", identifier="a", is_active=True)
    app_b = App.objects.create(name="App B", identifier="b", is_active=False)
    app_c = App.objects.create(name="App C", identifier="c", is_active=True)

    # when
    call_command("app_delete_all")

    # then
    app_a.refresh_from_db()
    app_b.refresh_from_db()
    app_c.refresh_from_db()

    assert app_a.is_active is False
    assert app_a.removed_at is not None

    assert app_b.is_active is False
    assert app_b.removed_at is not None

    assert app_c.is_active is False
    assert app_c.removed_at is not None


def test_app_delete_all_skips_already_removed_apps(db):
    # given
    active_app = App.objects.create(name="Active", identifier="active", is_active=True)
    removed_app = App.objects.create(
        name="Removed",
        identifier="removed",
        is_active=False,
        removed_at=timezone.now(),
    )
    removed_app.refresh_from_db()
    original_removed_at = removed_app.removed_at

    # when
    call_command("app_delete_all")

    # then
    active_app.refresh_from_db()
    removed_app.refresh_from_db()

    assert active_app.is_active is False
    assert active_app.removed_at is not None

    assert removed_app.is_active is False
    assert removed_app.removed_at == original_removed_at


def test_app_delete_all_with_no_apps_does_not_call_manager(
    db, _patched_plugins_manager
):
    # given
    assert not App.objects.exists()

    # when
    call_command("app_delete_all")

    # then
    _patched_plugins_manager.app_deleted.assert_not_called()


def test_app_delete_all_without_force_sync_calls_app_deleted_on_manager(
    db, _patched_plugins_manager, django_capture_on_commit_callbacks
):
    # given
    app_a = App.objects.create(name="App A", identifier="a", is_active=True)
    app_b = App.objects.create(name="App B", identifier="b", is_active=True)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_command("app_delete_all")

    # then
    app_a.refresh_from_db()
    app_b.refresh_from_db()

    assert app_a.removed_at is not None
    assert app_b.removed_at is not None
    assert _patched_plugins_manager.app_deleted.call_args_list == [
        call(app_a),
        call(app_b),
    ]


@patch("saleor.app.actions.send_webhook_request_async.apply")
def test_app_delete_all_with_force_sync_dispatches_sync_webhooks(
    mocked_apply, db, _patched_plugins_manager
):
    # given
    app_a = App.objects.create(name="App A", identifier="a", is_active=True)
    app_b = App.objects.create(name="App B", identifier="b", is_active=True)
    subscription_query = "subscription { event { ... on AppDeleted { app { id } } } }"
    for current_app in (app_a, app_b):
        webhook = Webhook.objects.create(
            name=f"hook-{current_app.identifier}",
            app=current_app,
            target_url=f"http://example.com/{current_app.identifier}",
            is_active=True,
            subscription_query=subscription_query,
        )
        webhook.events.create(event_type=WebhookEventAsyncType.APP_DELETED)

    # when
    call_command("app_delete_all", force_sync=True)

    # then
    app_a.refresh_from_db()
    app_b.refresh_from_db()

    assert app_a.removed_at is not None
    assert app_b.removed_at is not None
    _patched_plugins_manager.app_deleted.assert_not_called()

    deliveries = EventDelivery.objects.filter(
        event_type=WebhookEventAsyncType.APP_DELETED
    )
    assert deliveries.count() == 2
    delivery_pks = set(deliveries.values_list("pk", flat=True))
    called_pks = {
        call.kwargs["kwargs"]["event_delivery_id"]
        for call in mocked_apply.call_args_list
    }
    assert called_pks == delivery_pks


def _call_command_json_lines(name: str, *args: str) -> list[dict]:
    out = StringIO()
    call_command(name, *args, stdout=out)
    return [json.loads(line) for line in out.getvalue().splitlines()]


def _create_webhook(app: App, name: str, is_active: bool = True) -> Webhook:
    return Webhook.objects.create(
        name=name,
        app=app,
        target_url=f"https://example.com/{app.identifier}/{name}",
        is_active=is_active,
        secret_key="secret-key",
        custom_headers={"X-Secret": "secret-header"},
        subscription_query="subscription { event { ... on OrderCreated { order { id } } } }",
    )


def _app_record(app: App) -> dict:
    return {
        "kind": "app",
        "id": graphene.Node.to_global_id("App", app.pk),
        "identifier": app.identifier,
        "name": app.name,
        "is_active": app.is_active,
    }


def _webhook_record(webhook: Webhook, delivering: bool) -> dict:
    return {
        "kind": "webhook",
        "id": graphene.Node.to_global_id("Webhook", webhook.pk),
        "app_id": graphene.Node.to_global_id("App", webhook.app_id),
        "name": webhook.name,
        "target_url": webhook.target_url,
        "is_active": webhook.is_active,
        "app_is_active": webhook.app.is_active,
        "delivering": delivering,
    }


def test_app_list_outputs_not_removed_apps_with_their_webhooks(db):
    # given
    active_app = App.objects.create(name="Active", identifier="active", is_active=True)
    active_webhook = _create_webhook(active_app, "on")
    inactive_webhook = _create_webhook(active_app, "off", is_active=False)
    inactive_app = App.objects.create(
        name="Inactive", identifier="inactive", is_active=False
    )
    webhook_of_inactive_app = _create_webhook(inactive_app, "on")
    removed_app = App.objects.create(
        name="Removed", identifier="removed", removed_at=timezone.now()
    )
    _create_webhook(removed_app, "on")

    # when
    records = _call_command_json_lines("app_list")

    # then
    assert records == [
        _app_record(active_app),
        _webhook_record(active_webhook, delivering=True),
        _webhook_record(inactive_webhook, delivering=False),
        _app_record(inactive_app),
        _webhook_record(webhook_of_inactive_app, delivering=False),
    ]


def test_app_list_with_no_apps_outputs_nothing(db):
    # when
    records = _call_command_json_lines("app_list")

    # then
    assert records == []


@pytest.mark.parametrize("count", [1, 3])
def test_app_list_query_count_does_not_depend_on_number_of_objects(
    count, db, django_assert_num_queries
):
    # given
    for i in range(count):
        app = App.objects.create(name=f"App {i}", identifier=f"app-{i}")
        for j in range(count):
            _create_webhook(app, f"hook-{j}")

    # when
    with django_assert_num_queries(2):
        records = _call_command_json_lines("app_list")

    # then
    assert len(records) == count + count * count


APP_SET_ACTIVE_COMMAND_MODULE = "saleor.app.management.commands.app_set_active"


@pytest.fixture
def _patched_app_set_active_manager():
    with patch(
        f"{APP_SET_ACTIVE_COMMAND_MODULE}.get_plugins_manager"
    ) as mocked_get_manager:
        mocked_manager = Mock()
        mocked_get_manager.return_value = mocked_manager
        yield mocked_manager


@pytest.mark.parametrize(("before", "target"), [(True, False), (False, True)])
def test_app_set_active_changes_state_and_emits_status_changed(
    before,
    target,
    db,
    _patched_app_set_active_manager,
    django_capture_on_commit_callbacks,
):
    # given
    app = App.objects.create(name="App", identifier="app", is_active=before)
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        records = _call_command_json_lines(
            "app_set_active", "--id", app_id, "--active", str(target).lower()
        )

    # then
    app.refresh_from_db()
    assert app.is_active is target
    _patched_app_set_active_manager.app_status_changed.assert_called_once_with(app)
    assert records == [
        {
            "kind": "app",
            "id": app_id,
            "identifier": app.identifier,
            "name": app.name,
            "is_active": {"before": before, "after": target},
        }
    ]


@pytest.mark.parametrize("state", [True, False])
def test_app_set_active_same_state_does_not_emit_event(
    state, db, _patched_app_set_active_manager, django_capture_on_commit_callbacks
):
    # given
    app = App.objects.create(name="App", identifier="app", is_active=state)
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        records = _call_command_json_lines(
            "app_set_active", "--id", app_id, "--active", str(state).upper()
        )

    # then
    _patched_app_set_active_manager.app_status_changed.assert_not_called()
    assert records[0]["is_active"] == {"before": state, "after": state}


@pytest.mark.parametrize(
    ("_case", "global_id", "message"),
    [
        ("not_base64", "garbage", "Invalid ID: garbage."),
        (
            "wrong_type",
            graphene.Node.to_global_id("Webhook", 1),
            "Invalid ID: V2ViaG9vazox. Expected: App, received: Webhook.",
        ),
        (
            "non_int_pk",
            graphene.Node.to_global_id("App", "x"),
            "Invalid ID: QXBwOng=.",
        ),
        (
            "unknown_pk",
            graphene.Node.to_global_id("App", -1),
            "App not found: QXBwOi0x.",
        ),
    ],
)
def test_app_set_active_rejects_invalid_id(
    _case, global_id, message, db, _patched_app_set_active_manager
):
    # when
    with pytest.raises(CommandError) as exc_info:
        call_command("app_set_active", "--id", global_id, "--active", "false")

    # then
    assert str(exc_info.value) == message
    _patched_app_set_active_manager.app_status_changed.assert_not_called()


def test_app_set_active_rejects_removed_app(db, _patched_app_set_active_manager):
    # given
    app = App.objects.create(
        name="Removed", identifier="removed", is_active=True, removed_at=timezone.now()
    )
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    with pytest.raises(CommandError) as exc_info:
        call_command("app_set_active", "--id", app_id, "--active", "false")

    # then
    assert str(exc_info.value) == f"App not found: {app_id}."
    app.refresh_from_db()
    assert app.is_active is True
    _patched_app_set_active_manager.app_status_changed.assert_not_called()


@pytest.mark.parametrize("command", ["app_set_active", "webhook_set_active"])
@pytest.mark.parametrize("active", ["yes", "1", ""])
def test_set_active_rejects_non_boolean_active(command, active, db):
    # when
    with pytest.raises(CommandError) as exc_info:
        call_command(command, "--id", "unused", "--active", active)

    # then
    assert str(exc_info.value) == (
        f"Error: argument --active: expected 'true' or 'false', got {active!r}"
    )


@pytest.mark.parametrize(("before", "target"), [(True, False), (False, True)])
@pytest.mark.parametrize("app_is_active", [True, False])
def test_webhook_set_active_changes_state(before, target, app_is_active, db):
    # given
    app = App.objects.create(name="App", identifier="app", is_active=app_is_active)
    webhook = _create_webhook(app, "hook", is_active=before)
    other_webhook = _create_webhook(app, "other", is_active=before)
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)

    # when
    records = _call_command_json_lines(
        "webhook_set_active", "--id", webhook_id, "--active", str(target)
    )

    # then
    webhook.refresh_from_db()
    other_webhook.refresh_from_db()
    assert webhook.is_active is target
    assert other_webhook.is_active is before
    assert records == [
        {
            "kind": "webhook",
            "id": webhook_id,
            "app_id": graphene.Node.to_global_id("App", app.pk),
            "name": webhook.name,
            "is_active": {"before": before, "after": target},
        }
    ]


@pytest.mark.parametrize("state", [True, False])
def test_webhook_set_active_same_state_reports_no_change(state, db):
    # given
    app = App.objects.create(name="App", identifier="app", is_active=True)
    webhook = _create_webhook(app, "hook", is_active=state)
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)

    # when
    records = _call_command_json_lines(
        "webhook_set_active", "--id", webhook_id, "--active", str(state)
    )

    # then
    webhook.refresh_from_db()
    assert webhook.is_active is state
    assert records[0]["is_active"] == {"before": state, "after": state}


@pytest.mark.parametrize(
    ("_case", "global_id", "message"),
    [
        ("not_base64", "garbage", "Invalid ID: garbage."),
        (
            "wrong_type",
            graphene.Node.to_global_id("App", 1),
            "Invalid ID: QXBwOjE=. Expected: Webhook, received: App.",
        ),
        (
            "unknown_pk",
            graphene.Node.to_global_id("Webhook", -1),
            "Webhook not found: V2ViaG9vazotMQ==.",
        ),
    ],
)
def test_webhook_set_active_rejects_invalid_id(_case, global_id, message, db):
    # when
    with pytest.raises(CommandError) as exc_info:
        call_command("webhook_set_active", "--id", global_id, "--active", "false")

    # then
    assert str(exc_info.value) == message


def test_webhook_set_active_rejects_webhook_of_removed_app(db):
    # given
    app = App.objects.create(
        name="Removed", identifier="removed", removed_at=timezone.now()
    )
    webhook = _create_webhook(app, "hook", is_active=True)
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)

    # when
    with pytest.raises(CommandError) as exc_info:
        call_command("webhook_set_active", "--id", webhook_id, "--active", "false")

    # then
    assert str(exc_info.value) == f"Webhook not found: {webhook_id}."
    webhook.refresh_from_db()
    assert webhook.is_active is True
