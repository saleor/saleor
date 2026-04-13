import time
from unittest.mock import ANY, patch
from urllib.parse import urlencode

import graphene
from django.conf import settings
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.notifications import get_default_user_payload
from ......core.jwt import JWT_CONFIRM_CHANGE_EMAIL_TYPE, jwt_decode
from ......core.notify import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.utils.url import prepare_url
from .....tests.utils import get_graphql_content
from .conftest import CONFIRM_EMAIL_UPDATE_QUERY, REQUEST_EMAIL_CHANGE_QUERY


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
    expected_token_payload = {
        "old_email": customer_user.email,
        "email": customer_user.email,
        "new_email": new_email.lower(),
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "token": customer_user.jwt_token_key,
        "is_staff": False,
        "iat": time.time(),
        "exp": time.time() + settings.JWT_TTL_REQUEST_EMAIL_CHANGE.total_seconds(),
        "type": JWT_CONFIRM_CHANGE_EMAIL_TYPE,
        "owner": "saleor",
        "iss": "https://example.com/graphql/",
    }

    # when
    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestEmailChange"]
    assert not data["errors"]

    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": new_email.lower(),
        "token": ANY,
        "redirect_url": ANY,
        "old_email": customer_user.email,
        "new_email": new_email.lower(),
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_CHANGE_EMAIL_REQUEST
    assert len(called_kwargs) == 2
    assert called_kwargs["channel_slug"] == channel_PLN.slug

    payload = called_kwargs["payload_func"]()
    assert payload == expected_payload
    assert jwt_decode(payload["token"]) == expected_token_payload

    expected_redirect_url = prepare_url(
        urlencode({"token": payload["token"]}), redirect_url
    )
    assert payload["redirect_url"] == expected_redirect_url


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
    user_api_client,
    customer_user,
    staff_user,
    channel_PLN,
):
    """Ensure that we do not reveal a user's existence when requesting email change.

    We expect the following flow:
    1. Requesting changing the email to one that's already used, shouldn't error out
       (timing is also expected to be constant however this test doesn't verify it)
    2. The confirmation token is sent to 'new_email' in order to verify whether the
       user has access to 'new_email'
    3. Once the user clicks the link, they see 'Email is used by other user' error as
       they confirmed that they own or have access to 'new_email' thus it's safe to
       reveal that information
    """

    old_email = customer_user.email
    new_email = staff_user.email
    channel_slug = channel_PLN.slug

    variables = {
        "password": "password",
        "new_email": new_email,
        "redirect_url": "http://www.example.com",
        "channel": channel_slug,
    }

    # When requesting email change and the new email address exists
    # it should NOT return an error (we do not want to reveal whether
    # the user exists)

    with patch(
        "saleor.plugins.manager.PluginsManager.account_change_email_requested",
    ) as mocked_notify:
        response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestEmailChange"]
    assert data["user"] == {"email": customer_user.email}
    assert not data["errors"]

    # Retrieve the email change confirmation token
    mocked_notify.assert_called_once_with(
        customer_user,
        channel_slug,
        ANY,  # token
        ANY,  # redirect url
        new_email,
    )
    token: str = mocked_notify.call_args_list[0].args[2]
    assert isinstance(token, str)
    jwt_decode(token)  # ensure we grabbed a JWT and not something unrelated

    # When confirming the email change, it should error out when the user
    # already exists
    content = get_graphql_content(
        user_api_client.post_graphql(
            CONFIRM_EMAIL_UPDATE_QUERY, {"token": token, "channel": channel_slug}
        )
    )
    data = content["data"]["confirmEmailChange"]
    assert data == {
        "errors": [
            {
                "code": "UNIQUE",
                "field": "newEmail",
                "message": "Email is used by other user.",
            }
        ],
        "user": None,
    }

    customer_user.refresh_from_db(fields=("email",))
    assert customer_user.email == old_email, "Shouldn't have changed the email"


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


def test_request_email_change_but_no_channels_exist(user_api_client, customer_user):
    """It should return an error when no channel exist in DB."""
    variables = {
        "password": "password",
        "new_email": "new_email@example.com",
        "redirect_url": "http://www.example.com",
    }
    response = user_api_client.post_graphql(REQUEST_EMAIL_CHANGE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestEmailChange"]
    assert not data["user"]
    assert data["errors"] == [
        {
            "code": "MISSING_CHANNEL_SLUG",
            "message": "You need to provide channel slug.",
            "field": "channel",
        }
    ]
