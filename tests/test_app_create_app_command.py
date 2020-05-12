from unittest.mock import ANY, Mock

import pytest
import requests
from django.core.management import call_command

from saleor.app.models import App, AppJob
from saleor.core import JobStatus
from saleor.core.permissions import get_permissions


@pytest.mark.vcr
def test_creates_app_object():
    name = "Single App"
    manifest_url = "http://localhost:3000/manifest"
    permissions = ["account.manage_users", "order.manage_orders"]
    call_command("create_app", name, manifest_url, permission=permissions)

    apps = App.objects.filter(name=name)
    assert len(apps) == 1

    app = apps[0]
    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert not app.is_active


@pytest.mark.vcr
def test_activate_app():
    name = "Single App"
    manifest_url = "http://localhost:3000/manifest"
    permissions = ["account.manage_users", "order.manage_orders"]
    call_command(
        "create_app", name, manifest_url, permission=permissions, activate=True
    )

    apps = App.objects.filter(name=name)
    assert len(apps) == 1

    app = apps[0]
    tokens = app.tokens.all()
    assert len(tokens) == 1
    assert app.is_active


@pytest.mark.vcr
def test_app_has_all_required_permissions():
    name = "SA name"
    manifest_url = "http://localhost:3000/manifest"
    permission_list = ["account.manage_users", "order.manage_orders"]
    expected_permission = get_permissions(permission_list)
    call_command("create_app", name, manifest_url, permission=permission_list)

    apps = App.objects.filter(name=name)
    assert len(apps) == 1
    app = apps[0]
    assert set(app.permissions.all()) == set(expected_permission)


@pytest.mark.vcr
def test_create_app_sends_token(monkeypatch):
    mocked_response = Mock()
    mocked_response.status_code = 200
    mocked_post = Mock(return_value=mocked_response)

    monkeypatch.setattr(requests, "post", mocked_post)
    name = "Single App"
    manifest_url = "http://localhost:3000/manifest"
    permissions = [
        "account.manage_users",
    ]

    call_command("create_app", name, manifest_url, permission=permissions)

    app = App.objects.filter(name=name)[0]
    token = app.tokens.all()[0].auth_token
    mocked_post.assert_called_once_with(
        "http://localhost:3000/register",
        headers={"Content-Type": "application/json", "x-saleor-domain": "mirumee.com"},
        json={"auth_token": token},
        timeout=ANY,
    )


def test_schedule_installation_as_a_celery_task(monkeypatch):
    mocked_install_task = Mock()
    mocked_install = Mock()
    monkeypatch.setattr(
        "saleor.app.management.commands.create_app.install_app_task.delay",
        mocked_install_task,
    )
    monkeypatch.setattr(
        "saleor.app.management.commands.create_app.install_app", mocked_install
    )

    name = "Single App"
    manifest_url = "http://localhost:3000/manifest"
    permissions = ["account.manage_users", "order.manage_orders"]

    call_command(
        "create_app", name, manifest_url, permission=permissions, use_celery=True
    )

    app_job = AppJob.objects.get()
    assert not mocked_install.called
    mocked_install_task.assert_called_once_with(app_job.pk, False)


@pytest.mark.vcr
def test_installation_failed():
    name = "Single App"
    manifest_url = "http://localhost:3000/manifest"
    permissions = ["account.manage_users", "order.manage_orders"]

    with pytest.raises(Exception):
        call_command("create_app", name, manifest_url, permission=permissions)

    app_job = AppJob.objects.get()
    assert app_job.status == JobStatus.FAILED
