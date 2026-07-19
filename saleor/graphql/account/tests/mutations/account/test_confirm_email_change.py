from functools import partial
from unittest.mock import patch

from django.conf import settings

from ......account.models import User
from ......channel.models import Channel
from ......core.jwt import JWT_CONFIRM_CHANGE_EMAIL_TYPE, create_token, jwt_decode
from .....tests.fixtures import ApiClient
from .....tests.utils import get_graphql_content
from .conftest import CONFIRM_EMAIL_UPDATE_QUERY, REQUEST_EMAIL_CHANGE_QUERY


def request_email_change(
    *, user: User, client: ApiClient, new_email: str, channel: Channel
) -> str:
    old_email = user.email

    # Request a new token
    with patch(
        "saleor.plugins.manager.PluginsManager.account_change_email_requested",
    ) as mocked_notify:
        resp = get_graphql_content(
            client.post_graphql(
                REQUEST_EMAIL_CHANGE_QUERY,
                {
                    "new_email": new_email,
                    "redirect_url": "https://www.example.com",
                    "password": "password",
                    "channel": channel.slug,
                },
            )
        )

    # Sanitity check: shouldn't have altered the user
    assert resp["data"]["requestEmailChange"]["errors"] == []
    user.refresh_from_db(fields=("email",))
    assert user.email == old_email

    # Retrive the token
    mocked_notify.assert_called_once()
    token: str = mocked_notify.call_args_list[0].args[2]
    assert isinstance(token, str)
    jwt_decode(token)  # ensures it's a JWT
    return token


@patch(
    "saleor.graphql.account.mutations.account.confirm_email_change.match_orders_with_new_user"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_email_change.assign_user_gift_cards"
)
@patch("saleor.plugins.manager.PluginsManager.account_email_changed")
def test_email_update(
    mocked_account_email_changed,
    assign_gift_cards_mock,
    assign_orders_mock,
    user_api_client,
    customer_user,
    channel_PLN,
):
    new_email = "new_email@example.com"
    payload = {
        "old_email": customer_user.email,
        "new_email": new_email,
        "user_pk": customer_user.pk,
    }
    user = user_api_client.user

    token = create_token(
        payload,
        exp_delta=settings.JWT_TTL_REQUEST_EMAIL_CHANGE,
        token_type=JWT_CONFIRM_CHANGE_EMAIL_TYPE,
        user=customer_user,
    )
    variables = {"token": token, "channel": channel_PLN.slug}
    response = user_api_client.post_graphql(CONFIRM_EMAIL_UPDATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["confirmEmailChange"]
    assert data["user"]["email"] == new_email
    user.refresh_from_db()
    assert user.search_vector
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    assign_orders_mock.assert_called_once_with(customer_user)
    mocked_account_email_changed.assert_called_once_with(user)


def test_email_update_to_existing_email(user_api_client, customer_user, staff_user):
    payload = {
        "old_email": customer_user.email,
        "new_email": staff_user.email,
        "user_pk": customer_user.pk,
    }
    token = create_token(
        payload,
        exp_delta=settings.JWT_TTL_REQUEST_EMAIL_CHANGE,
        token_type=JWT_CONFIRM_CHANGE_EMAIL_TYPE,
        user=customer_user,
    )
    variables = {"token": token}

    response = user_api_client.post_graphql(CONFIRM_EMAIL_UPDATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["confirmEmailChange"]
    assert not data["user"]
    assert data["errors"] == [
        {
            "code": "UNIQUE",
            "message": "Email is used by other user.",
            "field": "newEmail",
        }
    ]


@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_account_email_changed_webhook_event_triggered(
    mocked_trigger_webhooks_async,
    settings,
    customer_user,
    user_api_client,
    subscription_account_email_changed_webhook,
    channel_PLN,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    new_email = "new_email@example.com"
    payload = {
        "old_email": customer_user.email,
        "new_email": new_email,
        "user_pk": customer_user.pk,
    }
    user = user_api_client.user

    token = create_token(
        payload,
        exp_delta=settings.JWT_TTL_REQUEST_EMAIL_CHANGE,
        token_type=JWT_CONFIRM_CHANGE_EMAIL_TYPE,
        user=customer_user,
    )
    variables = {"token": token, "channel": channel_PLN.slug}

    # when
    user_api_client.post_graphql(CONFIRM_EMAIL_UPDATE_QUERY, variables)

    # then
    user.refresh_from_db()
    assert user.search_vector

    mocked_trigger_webhooks_async.assert_called()


def test_confirm_email_change_other_user_token(
    user_api_client,
    user2_api_client,
    channel_USD,
    customer_user,
):
    old_email = customer_user.email
    new_email = "new-email@example.com"

    confirm_email_change_vars = {
        "token": request_email_change(
            user=customer_user,
            client=user_api_client,
            channel=channel_USD,
            new_email=new_email,
        ),
        "channel": channel_USD.slug,
    }

    # Ensure 'user2_api_client' cannot use token of 'user_api_client'
    resp = get_graphql_content(
        user2_api_client.post_graphql(
            CONFIRM_EMAIL_UPDATE_QUERY, confirm_email_change_vars
        )
    )
    assert resp["data"]["confirmEmailChange"]["errors"] == [
        {"message": "Invalid token.", "field": "token", "code": "JWT_INVALID_TOKEN"}
    ]

    # It shouldn't have altered the email
    customer_user.refresh_from_db(fields=("email",))
    assert customer_user.email == old_email

    # Sanity check: ensure 'user_api_client' can use the token generated by 'user_api_client'
    resp = get_graphql_content(
        user_api_client.post_graphql(
            CONFIRM_EMAIL_UPDATE_QUERY, confirm_email_change_vars
        )
    )
    assert resp["data"]["confirmEmailChange"]["errors"] == []
    customer_user.refresh_from_db(fields=("email",))
    assert customer_user.email == new_email


def test_cannot_confirm_email_change_if_old_email_mismatches(
    user_api_client,
    channel_USD,
    customer_user,
):
    """Ensure when 'old_email' doesn't match user.email, then it aborts."""

    new_email = "new-email@example.com"

    confirm_email_change_vars = {
        "token": request_email_change(
            user=customer_user,
            client=user_api_client,
            channel=channel_USD,
            new_email=new_email,
        ),
        "channel": channel_USD.slug,
    }

    send_confirm_change = partial(
        user_api_client.post_graphql,
        CONFIRM_EMAIL_UPDATE_QUERY,
        confirm_email_change_vars,
    )

    # Should accept the token when using it for the first time
    resp = send_confirm_change().json()
    assert resp["data"]["confirmEmailChange"]["errors"] == [], resp
    customer_user.refresh_from_db(fields=("email",))
    assert customer_user.email == new_email

    resp = send_confirm_change().json()
    errors = resp["errors"]
    assert len(errors) == 1
    assert errors[0]["message"] == "Invalid token. User does not exist or is inactive."
    customer_user.refresh_from_db(fields=("email",))
    assert customer_user.email == new_email
