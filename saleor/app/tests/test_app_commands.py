from unittest.mock import ANY, Mock, call

import pytest
from django.core.management import call_command
from requests_hardened import HTTPSession

from ... import schema_version
from ...core import JobStatus
from ...permission.enums import get_permissions
from ..models import App, AppInstallation


@pytest.mark.vcr
def test_creates_app_from_manifest():
    manifest_url = "http://otherapp:3000/manifest"
    call_command("install_app", manifest_url)

    app = App.objects.get()

    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert not app.is_active
    assert app.uuid is not None


@pytest.mark.vcr
def test_creates_app_from_manifest_activate_app():
    manifest_url = "http://otherapp:3000/manifest"
    call_command("install_app", manifest_url, activate=True)

    app = App.objects.get()

    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert app.is_active


@pytest.mark.vcr
def test_creates_app_from_manifest_app_has_all_required_permissions():
    manifest_url = "http://localhost:3000/manifest"
    permission_list = ["account.manage_users", "order.manage_orders"]
    expected_permission = get_permissions(permission_list)
    call_command("install_app", manifest_url)

    app = App.objects.get()
    assert set(app.permissions.all()) == set(expected_permission)


def test_creates_app_from_manifest_sends_token(monkeypatch, app_manifest):
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

    call_command("install_app", manifest_url)

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
            "X-Saleor-Domain": "mirumee.com",
            "Saleor-Domain": "mirumee.com",
            "Saleor-Api-Url": "http://mirumee.com/graphql/",
            "Saleor-Schema-Version": schema_version,
        },
        json={"auth_token": ANY},
        timeout=ANY,
        allow_redirects=False,
    )


@pytest.mark.vcr
def test_creates_app_from_manifest_installation_failed():
    manifest_url = "http://localhost:3000/manifest-wrong"

    with pytest.raises(Exception):
        call_command("install_app", manifest_url)

    app_job = AppInstallation.objects.get()
    assert app_job.status == JobStatus.FAILED
    assert app_job.uuid is not None


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
            "X-Saleor-Domain": "mirumee.com",
            "Saleor-Domain": "mirumee.com",
            "Saleor-Api-Url": "http://mirumee.com/graphql/",
            "Saleor-Schema-Version": schema_version,
        },
        json={"auth_token": ANY},
        timeout=ANY,
        allow_redirects=False,
    )
