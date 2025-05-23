from unittest import mock
from urllib.parse import urlencode

import pytest

from ...core.notify import NotifyEventType, UserNotifyEvent
from ...core.tests.utils import get_site_context_payload
from ...core.utils.url import prepare_url
from ...graphql.core.utils import to_global_id_or_none
from ...plugins.manager import get_plugins_manager
from .. import notifications
from ..notifications import get_default_user_payload


def test_get_default_user_payload(customer_user):
    assert get_default_user_payload(customer_user) == {
        "id": to_global_id_or_none(customer_user),
        "email": customer_user.email,
        "first_name": customer_user.first_name,
        "last_name": customer_user.last_name,
        "is_staff": customer_user.is_staff,
        "is_active": customer_user.is_active,
        "private_metadata": {},
        "metadata": customer_user.metadata,
        "language_code": customer_user.language_code,
    }


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_request_change(
    mocked_notify, site_settings, customer_user, channel_PLN
):
    # given
    new_email = "example@example.com"
    redirect_url = "http://localhost:8000/redirect"
    token = "token_example"

    manager = get_plugins_manager(allow_replica=False)

    # when
    notifications.send_request_user_change_email_notification(
        redirect_url,
        customer_user,
        new_email,
        token,
        manager,
        channel_slug=channel_PLN.slug,
    )

    # then
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": new_email,
        "token": token,
        "redirect_url": f"{redirect_url}?token={token}",
        "old_email": customer_user.email,
        "new_email": new_email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }
    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_changed_notification(
    mocked_notify, site_settings, customer_user, channel_PLN
):
    # given
    old_email = "example@example.com"

    # when
    notifications.send_user_change_email_notification(
        old_email,
        customer_user,
        get_plugins_manager(allow_replica=False),
        channel_slug=channel_PLN.slug,
    )

    # then
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": old_email,
        "channel_slug": channel_PLN.slug,
        "old_email": old_email,
        "new_email": customer_user.email,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_CONFIRM
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug


@pytest.mark.parametrize("is_staff", [True, False])
@mock.patch("saleor.account.notifications.token_generator.make_token")
@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_password_reset_notification(
    mocked_notify, mocked_generator, is_staff, site_settings, customer_user, channel_PLN
):
    # given
    token = "token_example"
    mocked_generator.return_value = token
    redirect_url = "http://localhost:8000/reset"
    params = urlencode({"email": customer_user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)

    # when
    notifications.send_password_reset_notification(
        redirect_url,
        customer_user,
        get_plugins_manager(allow_replica=False),
        channel_slug=channel_PLN.slug,
        staff=is_staff,
    )

    # then
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": customer_user.email,
        "token": token,
        "reset_url": reset_url,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }
    expected_event = (
        NotifyEventType.ACCOUNT_STAFF_RESET_PASSWORD
        if is_staff
        else NotifyEventType.ACCOUNT_PASSWORD_RESET
    )

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == expected_event
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug
