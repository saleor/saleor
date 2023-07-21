import datetime
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from ......account.error_codes import SendConfirmationEmailErrorCode
from ......account.notifications import get_default_user_payload
from ......core.notify_events import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.utils.url import prepare_url
from .....tests.utils import get_graphql_content

SEND_CONFIRMATION_EMAIL_MUTATION = """
    mutation SendConfirmationEmail(
        $redirectUrl: String!, $channel: String!) {
        sendConfirmationEmail(
            redirectUrl: $redirectUrl, channel: $channel) {
            errors {
                field
                message
                code
            }
        }
    }
"""


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_email(
    mocked_notify,
    user_api_client,
    channel_PLN,
    site_settings,
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    user = user_api_client.user
    user.is_confirmed = False
    user.save(update_fields=["is_confirmed"])

    # when
    response = user_api_client.post_graphql(SEND_CONFIRMATION_EMAIL_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["sendConfirmationEmail"]
    assert not data["errors"]

    token = default_token_generator.make_token(user)
    params = urlencode({"email": user.email, "token": token})
    confirm_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(user),
        "token": token,
        "confirm_url": confirm_url,
        "recipient_email": user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_CONFIRMATION,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )
    user.refresh_from_db()
    assert user.last_confirm_email_request == timezone.now()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_email_on_cooldown(
    mocked_notify, user_api_client, channel_PLN
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    user = user_api_client.user
    user.last_confirm_email_request = timezone.now()
    user.is_confirmed = False
    user.save(update_fields=["last_confirm_email_request", "is_confirmed"])

    # when
    response = user_api_client.post_graphql(SEND_CONFIRMATION_EMAIL_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["sendConfirmationEmail"]["errors"]
    assert errors == [
        {
            "field": None,
            "message": "Confirmation email already requested",
            "code": SendConfirmationEmailErrorCode.CONFIRMATION_ALREADY_REQUESTED.name,
        }
    ]
    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
def test_send_confirmation_email_after_cooldown(user_api_client, channel_PLN, settings):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    user = user_api_client.user
    user.last_confirm_email_request = timezone.now() - datetime.timedelta(
        seconds=settings.CONFIRMATION_EMAIL_LOCK_TIME
    )
    user.is_confirmed = False
    user.save(update_fields=["last_confirm_email_request", "is_confirmed"])

    # when
    response = user_api_client.post_graphql(SEND_CONFIRMATION_EMAIL_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["sendConfirmationEmail"]["errors"]) == 0


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_email_user_already_confirmed(
    mocked_notify, user_api_client, channel_PLN
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    response = user_api_client.post_graphql(SEND_CONFIRMATION_EMAIL_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["sendConfirmationEmail"]["errors"]
    assert errors == [
        {
            "field": None,
            "message": "User is already confirmed",
            "code": SendConfirmationEmailErrorCode.ACCOUNT_CONFIRMED.name,
        }
    ]
    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
@override_settings(ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL=False)
def test_send_confirmation_email_confirmation_disabled(
    mocked_notify, user_api_client, channel_PLN
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    response = user_api_client.post_graphql(SEND_CONFIRMATION_EMAIL_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["sendConfirmationEmail"]["errors"]
    assert errors == [
        {
            "field": None,
            "message": "User is already confirmed",
            "code": SendConfirmationEmailErrorCode.ACCOUNT_CONFIRMED.name,
        }
    ]
    mocked_notify.assert_not_called()


@override_settings(
    ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL=True,
    ALLOWED_CLIENT_HOSTS=["localhost"],
)
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_email_generates_valid_token(
    mocked_notify,
    user_api_client,
    channel_PLN,
):
    # given
    redirect_url = "http://localhost:3000"
    variables = {
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    user = user_api_client.user
    user.is_confirmed = False
    user.save()

    # when
    response = user_api_client.post_graphql(SEND_CONFIRMATION_EMAIL_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["sendConfirmationEmail"]["errors"]

    token = mocked_notify.call_args.kwargs["payload"]["token"]
    user.refresh_from_db()
    assert default_token_generator.check_token(user, token)
