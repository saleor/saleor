from unittest.mock import ANY, Mock

import requests
from django.core.management import call_command

from saleor.app.models import App
from saleor.core.permissions import get_permissions


def test_creates_app_object():
    name = "Single App"
    permissions = ["account.manage_users", "order.manage_orders"]
    call_command("create_app", name, permission=permissions)

    apps = App.objects.filter(name=name)
    assert len(apps) == 1

    app = apps[0]
    tokens = app.tokens.all()
    assert len(tokens) == 1


def test_app_has_all_required_permissions():
    name = "SA name"
    permission_list = ["account.manage_users", "order.manage_orders"]
    expected_permission = get_permissions(permission_list)
    call_command("create_app", name, permission=permission_list)

    apps = App.objects.filter(name=name)
    assert len(apps) == 1
    app = apps[0]
    assert set(app.permissions.all()) == set(expected_permission)


def test_sends_data_to_target_url(monkeypatch):
    mocked_response = Mock()
    mocked_response.status_code = 200
    mocked_post = Mock(return_value=mocked_response)

    monkeypatch.setattr(requests, "post", mocked_post)

    name = "Single App"
    target_url = "https://ss.shop.com/register"
    permissions = [
        "account.manage_users",
    ]

    call_command("create_app", name, permission=permissions, target_url=target_url)

    app = App.objects.filter(name=name)[0]
    token = app.tokens.all()[0].auth_token
    mocked_post.assert_called_once_with(
        target_url,
        headers={"x-saleor-domain": "mirumee.com"},
        json={"auth_token": token},
        timeout=ANY,
    )
