from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.notifications import get_default_user_payload
from ......core.jwt import create_token
from ......core.notify_events import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.utils.url import prepare_url
from .....tests.utils import get_graphql_content

REQUEST_EMAIL_CHANGE_QUERY = """
mutation requestEmailChange(
    $password: String!, $new_email: String!, $redirect_url: String!, $channel:String
) {
    requestEmailChange(
        password: $password,
        newEmail: $new_email,
        redirectUrl: $redirect_url,
        channel: $channel
    ) {
        user {
            email
        }
        errors {
            code
            message
            field
        }
  }
}
"""


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_request_email_change_with_upper_case_email(
    mocked_notify,
    user_api_client,
    customer_user,
    site_settings,
    channel_PLN,
):
    # given
    new_email = "NEW_EMAIL@example.com"
    redirect_url = "https://www.example.com"
    variables = {
        "new_email": new_email,
        "redirect_url": redirect_url,
        "password": "password",
        "channel": channel_PLN.slug,
    }
    token_payload = {
        "old_email": customer_user.email,
        "new_email": new_email.lower(),
        "user_pk": customer_user.pk,
    }
    token = create_token(token_payload, settings.JWT_TTL_REQUEST_EMAIL_CHANGE)

    # when
    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestEmailChange"]
    assert not data["errors"]

    params = urlencode({"token": token})
    redirect_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": new_email.lower(),
        "token": token,
        "redirect_url": redirect_url,
        "old_email": customer_user.email,
        "new_email": new_email.lower(),
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_CHANGE_EMAIL_REQUEST,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


def test_request_email_change(user_api_client, customer_user, channel_PLN):
    variables = {
        "password": "password",
        "new_email": "new_email@example.com",
        "redirect_url": "http://www.example.com",
        "channel": channel_PLN.slug,
    }

    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestEmailChange"]
    assert data["user"]["email"] == customer_user.email


def test_request_email_change_to_existing_email(
    user_api_client, customer_user, staff_user
):
    variables = {
        "password": "password",
        "new_email": staff_user.email,
        "redirect_url": "http://www.example.com",
    }

    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestEmailChange"]
    assert not data["user"]
    assert data["errors"] == [
        {
            "code": "UNIQUE",
            "message": "Email is used by other user.",
            "field": "newEmail",
        }
    ]


def test_request_email_change_with_invalid_redirect_url(
    user_api_client, customer_user, staff_user
):
    variables = {
        "password": "password",
        "new_email": "new_email@example.com",
        "redirect_url": "www.example.com",
    }

    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestEmailChange"]
    assert not data["user"]
    assert data["errors"] == [
        {
            "code": "INVALID",
            "message": "Invalid URL. Please check if URL is in RFC 1808 format.",
            "field": "redirectUrl",
        }
    ]


def test_request_email_change_with_invalid_password(user_api_client, customer_user):
    variables = {
        "password": "spanishinquisition",
        "new_email": "new_email@example.com",
        "redirect_url": "http://www.example.com",
    }
    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestEmailChange"]
    assert not data["user"]
    assert data["errors"][0]["code"] == AccountErrorCode.INVALID_CREDENTIALS.name
    assert data["errors"][0]["field"] == "password"


@patch("saleor.graphql.account.mutations.account.request_email_change.create_token")
@patch("saleor.plugins.manager.PluginsManager.account_change_email_requested")
def test_request_email_change_send_event(
    account_change_email_requested_mock,
    create_token_mock,
    user_api_client,
    customer_user,
    channel_PLN,
):
    create_token_mock.return_value = "token"
    redirect_url = "http://www.example.com"
    new_email = "new_email@example.com"
    variables = {
        "password": "password",
        "new_email": new_email,
        "redirect_url": redirect_url,
        "channel": channel_PLN.slug,
    }

    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestEmailChange"]
    assert data["user"]["email"] == customer_user.email

    params = urlencode({"token": "token"})
    change_email_url = prepare_url(params, redirect_url)

    account_change_email_requested_mock.assert_called_once_with(
        customer_user, channel_PLN.slug, "token", change_email_url, new_email
    )
