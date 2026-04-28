from unittest.mock import ANY, Mock, call, patch

import graphene
import pytest
from django.core.management import call_command
from django.forms import ValidationError
from django.utils import timezone
from requests_hardened import HTTPSession

from ... import schema_version
from ...core import JobStatus
from ...permission.enums import get_permissions
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
def _patched_app_delete_all():
    with patch(f"{APP_DELETE_ALL_COMMAND_MODULE}.delete_app") as mocked_delete_app:
        with patch(
            f"{APP_DELETE_ALL_COMMAND_MODULE}.get_plugins_manager"
        ) as mocked_get_manager:
            mocked_manager = Mock()
            mocked_get_manager.return_value = mocked_manager
            yield mocked_delete_app, mocked_manager


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


def test_app_delete_all_skips_already_removed_apps(db, _patched_app_delete_all):
    # given
    mocked_delete_app, mocked_manager = _patched_app_delete_all
    active_app = App.objects.create(name="Active", identifier="active", is_active=True)
    App.objects.create(
        name="Removed",
        identifier="removed",
        is_active=False,
        removed_at=timezone.now(),
    )

    # when
    call_command("app_delete_all")

    # then
    assert mocked_delete_app.call_count == 1
    mocked_delete_app.assert_called_once_with(
        active_app, mocked_manager, force_sync=False
    )


def test_app_delete_all_with_no_apps(db, _patched_app_delete_all):
    # given
    mocked_delete_app, _ = _patched_app_delete_all

    # when
    call_command("app_delete_all")

    # then
    mocked_delete_app.assert_not_called()


def test_app_delete_all_with_force_sync(db, _patched_app_delete_all):
    # given
    mocked_delete_app, mocked_manager = _patched_app_delete_all
    app_a = App.objects.create(name="App A", identifier="a", is_active=True)
    app_b = App.objects.create(name="App B", identifier="b", is_active=True)

    # when
    call_command("app_delete_all", force_sync=True)

    # then
    assert mocked_delete_app.call_args_list == [
        call(app_a, mocked_manager, force_sync=True),
        call(app_b, mocked_manager, force_sync=True),
    ]
