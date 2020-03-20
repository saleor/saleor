from unittest.mock import ANY, Mock

import requests
from django.core.management import call_command

from saleor.account.models import ServiceAccount
from saleor.core.permissions import get_permissions


def test_createaccount_command_creates_service_account():
    name = "SA name"
    permissions = ["account.manage_users", "order.manage_orders"]
    call_command("createserviceaccount", name, permission=permissions)

    sa_accounts = ServiceAccount.objects.filter(name=name)
    assert len(sa_accounts) == 1

    sa_account = sa_accounts[0]
    tokens = sa_account.tokens.all()
    assert len(tokens) == 1


def test_createaccount_command_service_account_has_all_required_permissions():
    name = "SA name"
    permission_list = ["account.manage_users", "order.manage_orders"]
    expected_permission = get_permissions(permission_list)
    call_command("createserviceaccount", name, permission=permission_list)

    sa_accounts = ServiceAccount.objects.filter(name=name)
    assert len(sa_accounts) == 1
    sa_account = sa_accounts[0]
    assert set(sa_account.permissions.all()) == set(expected_permission)


def test_createaccount_command_sends_data_to_target_url(monkeypatch):
    mocked_response = Mock()
    mocked_response.status_code = 200
    mocked_post = Mock(return_value=mocked_response)

    monkeypatch.setattr(requests, "post", mocked_post)

    name = "SA name"
    target_url = "https://ss.shop.com/register"
    permissions = [
        "account.manage_users",
    ]

    call_command(
        "createserviceaccount", name, permission=permissions, target_url=target_url
    )

    service_account = ServiceAccount.objects.filter(name=name)[0]
    token = service_account.tokens.all()[0].auth_token
    mocked_post.assert_called_once_with(
        target_url,
        headers={"x-saleor-domain": "mirumee.com"},
        json={"auth_token": token},
        timeout=ANY,
    )
