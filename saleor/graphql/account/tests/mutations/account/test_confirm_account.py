import functools
from typing import Any
from unittest import mock
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......core.tokens import (
    account_confirm_token_generator,
    legacy_account_confirm_token_generator,
    password_reset_token_generator,
)
from .....tests.utils import get_graphql_content, get_graphql_content_from_response

CONFIRM_ACCOUNT_MUTATION = """
    mutation ConfirmAccount($email: String!, $token: String!, $password: String!) {
        confirmAccount(email: $email, token: $token, password: $password) {
            errors {
                field
                code
                message
            }
            user {
                id
                email
            }
        }
    }
"""

WRONG_PASSWORD_ERROR = {
    "field": "password",
    "code": "INVALID",
    "message": "Invalid password",
}


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.account_confirmed")
def test_account_confirmation(
    mocked_account_confirmed,
    api_client,
    customer_user,
    channel_USD,
    site_settings,
    order,
    gift_card,
    throttling_disabled,
):
    customer_user.is_confirmed = False
    customer_user.save()

    # Create anonymous objects assigned to the targeted email
    order.user = gift_card.created_by = None
    order.user_email = gift_card.created_by_email = customer_user.email
    gift_card.save(update_fields=["created_by", "created_by_email"])
    order.save(update_fields=["user", "user_email"])

    variables = {
        "email": customer_user.email,
        "token": account_confirm_token_generator.make_token(customer_user),
        "channel": channel_USD.slug,
        "password": "password",
    }
    response = api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    content = get_graphql_content(response)
    assert not content["data"]["confirmAccount"]["errors"]
    assert content["data"]["confirmAccount"]["user"]["email"] == customer_user.email
    customer_user.refresh_from_db()

    assert customer_user.is_confirmed is True, "should have confirmed the the user"
    mocked_account_confirmed.assert_called_once_with(customer_user)

    gift_card.refresh_from_db(fields=("created_by", "created_by_email"))
    order.refresh_from_db(fields=("user", "user_email"))

    # In both cases, it shouldn't touch the email address
    assert gift_card.created_by_email == customer_user.email
    assert order.user_email == customer_user.email

    assert order.user == customer_user, "should have merged the order"
    assert gift_card.created_by == customer_user, "should have merged the gift card"


@freeze_time("2018-05-31 12:00:01")
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
def test_account_confirmation_invalid_user(
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    user_api_client,
    customer_user,
    channel_USD,
):
    variables = {
        "email": "non-existing@example.com",
        "token": account_confirm_token_generator.make_token(customer_user),
        "channel": channel_USD.slug,
        "password": "password",
    }
    response = user_api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["confirmAccount"]["errors"][0]["field"] == "token"
    assert (
        content["data"]["confirmAccount"]["errors"][0]["code"]
        == AccountErrorCode.INVALID.name
    )
    match_orders_with_new_user_mock.assert_not_called()
    assign_gift_cards_mock.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "input_data", "expected_errors"),
    [
        (
            "Missing 'password' field",
            {},
            (
                'Argument "password" of required type String!" provided the variable '
                '"$password" which was not provided'
            ),
        ),
        (
            "Null password",
            {"password": None},
            'Variable "$password" of required type "String!" was not provided.',
        ),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.account_confirmed")
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
def test_account_confirmation_requires_password_input(
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    account_confirmed_mock,
    _case,
    input_data,
    expected_errors,
    api_client,
    customer_user,
    order,
    gift_card,
):
    customer_user.is_confirmed = False
    customer_user.save(update_fields=("is_confirmed",))

    order.user = gift_card.created_by = None
    order.user_email = gift_card.created_by_email = customer_user.email
    gift_card.save(update_fields=["created_by", "created_by_email"])
    order.save(update_fields=["user", "user_email"])

    variables = {
        "email": customer_user.email,
        "token": account_confirm_token_generator.make_token(customer_user),
        **input_data,
    }

    response = api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)

    assert response.status_code == 400
    content = get_graphql_content_from_response(response)
    errors = content["errors"]
    assert len(errors) == 1
    assert errors[0]["message"] == expected_errors
    assert "data" not in content

    customer_user.refresh_from_db(fields=("is_confirmed",))
    order.refresh_from_db(fields=("user", "user_email"))
    gift_card.refresh_from_db(fields=("created_by", "created_by_email"))
    assert customer_user.is_confirmed is False
    assert order.user is None
    assert order.user_email == customer_user.email
    assert gift_card.created_by is None
    assert gift_card.created_by_email == customer_user.email
    match_orders_with_new_user_mock.assert_not_called()
    assign_gift_cards_mock.assert_not_called()
    account_confirmed_mock.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "input_data", "expected_errors"),
    [
        (
            "Invalid password",
            {"password": "hunter2"},
            [WRONG_PASSWORD_ERROR],
        ),
        (
            "Empty password",
            {"password": ""},
            [WRONG_PASSWORD_ERROR],
        ),
        (
            # Note: per GraphQL specs, Graphene is automatically casting non-string
            #       values to a string (https://spec.graphql.org/June2018/#sec-String)
            #       ("GraphQL servers may coerce non‐string raw values to String [...]")
            "Password is not a string",
            {"password": True},
            [WRONG_PASSWORD_ERROR],
        ),
    ],
)
def test_account_confirmation_requires_valid_password(
    _case: str,
    input_data: dict[str, Any],
    expected_errors: list[dict[str, Any]],
    api_client,
    customer_user,
    channel_USD,
    site_settings,
    order,
    gift_card,
    throttling_disabled,
):
    customer_user.is_confirmed = False
    customer_user.save(update_fields=("is_confirmed",))

    # Create anonymous objects assigned to the targeted email
    order.user = gift_card.created_by = None
    order.user_email = gift_card.created_by_email = customer_user.email
    gift_card.save(update_fields=["created_by", "created_by_email"])
    order.save(update_fields=["user", "user_email"])

    variables = {
        "email": customer_user.email,
        "token": account_confirm_token_generator.make_token(customer_user),
        "channel": channel_USD.slug,
        **input_data,
    }

    with mock.patch("saleor.account.throttling.cache", side_effect=1):
        response = api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["confirmAccount"]["errors"] == expected_errors
    assert content["data"]["confirmAccount"]["user"] is None
    customer_user.refresh_from_db(fields=("is_confirmed",))

    assert customer_user.is_confirmed is False, "shouldn't have confirmed the the user"

    # Ensure it didn't merge anonymous objects
    gift_card.refresh_from_db(fields=("created_by", "created_by_email"))
    order.refresh_from_db(fields=("user", "user_email"))
    assert gift_card.created_by_email == customer_user.email
    assert order.user_email == customer_user.email
    assert order.user is None, "shouldn't have merged the order"
    assert gift_card.created_by is None, "shouldn't have merged the gift card"


def test_account_confirmation_rate_limits_password(
    cache_clear,
    api_client,
    customer_user,
    channel_USD,
):
    """Account confirmation attempts with a valid token should be rate-limited."""

    customer_user.is_confirmed = False
    customer_user.save(update_fields=("is_confirmed",))

    variables = {
        "email": customer_user.email,
        "token": account_confirm_token_generator.make_token(customer_user),
        "channel": channel_USD.slug,
        "password": "invalid",
    }

    send_request = functools.partial(
        api_client.post_graphql, CONFIRM_ACCOUNT_MUTATION, variables
    )

    # 1st request should work (wrong password error)
    content = get_graphql_content(send_request())
    assert content["data"]["confirmAccount"]["errors"] == [WRONG_PASSWORD_ERROR]
    assert content["data"]["confirmAccount"]["user"] is None

    # 2nd request shouldn't work due to sending a new attempt too quickly
    content = get_graphql_content(send_request())
    assert content["data"]["confirmAccount"]["user"] is None
    errors = content["data"]["confirmAccount"]["errors"]
    assert errors == [
        {
            "field": None,
            "code": "LOGIN_ATTEMPT_DELAYED",
            "message": mock.ANY,
        }
    ]
    assert "too many logging attempts" in errors[0]["message"]


@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
def test_account_confirmation_invalid_token(
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    user_api_client,
    customer_user,
    channel_USD,
):
    variables = {
        "email": customer_user.email,
        "token": "invalid_token",
        "channel": channel_USD.slug,
        "password": "password",
    }
    response = user_api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["confirmAccount"]["errors"][0]["field"] == "token"
    assert (
        content["data"]["confirmAccount"]["errors"][0]["code"]
        == AccountErrorCode.INVALID.name
    )
    match_orders_with_new_user_mock.assert_not_called()
    assign_gift_cards_mock.assert_not_called()


@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
@patch("saleor.plugins.manager.PluginsManager.account_confirmed")
def test_account_confirmation_rejects_token_for_wrong_scope(
    mocked_account_confirmed,
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    user_api_client,
    customer_user,
    throttling_disabled,
):
    """When providing a token that's meant for another mutation, it should reject.

    In this test, we pass a password reset token instead of an account confirmation
    token, and we test whether it rejects it properly.
    """

    customer_user.is_confirmed = False
    customer_user.save(update_fields=["is_confirmed"])

    # Create token for the wrong mutation
    invalid_token = password_reset_token_generator.make_token(customer_user)
    variables = {
        "email": customer_user.email,
        "token": invalid_token,
        "password": "password",
    }

    # Should reject the token
    content = get_graphql_content(
        user_api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    )
    data = content["data"]["confirmAccount"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "token"
    assert data["errors"][0]["code"] == AccountErrorCode.INVALID.name

    # Shouldn't have confirmed the account nor merged the account
    customer_user.refresh_from_db(fields=("is_confirmed",))
    assert customer_user.is_confirmed is False
    match_orders_with_new_user_mock.assert_not_called()
    assign_gift_cards_mock.assert_not_called()
    mocked_account_confirmed.assert_not_called()

    # Sanity check: a valid token should work properly
    valid_token = account_confirm_token_generator.make_token(customer_user)
    variables["token"] = valid_token
    content = get_graphql_content(
        user_api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    )
    data = content["data"]["confirmAccount"]
    assert not data["errors"]

    # Should have merged the account & confirmed the account
    customer_user.refresh_from_db(fields=("is_confirmed",))
    assert customer_user.is_confirmed is True
    match_orders_with_new_user_mock.assert_called_once_with(customer_user)
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    mocked_account_confirmed.assert_called_once_with(customer_user)


@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
@patch("saleor.plugins.manager.PluginsManager.account_confirmed")
def test_account_confirmation_accepts_legacy_account_confirm_token(
    mocked_account_confirmed,
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    user_api_client,
    customer_user,
    throttling_disabled,
):
    """Ensure old tokens before adding scopes still work properly."""

    # given
    customer_user.is_confirmed = False
    customer_user.save(update_fields=["is_confirmed"])
    token = legacy_account_confirm_token_generator.make_token(customer_user)
    variables = {
        "email": customer_user.email,
        "token": token,
        "password": "password",
    }

    # when
    response = user_api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["confirmAccount"]
    assert not data["errors"]
    assert data["user"]["email"] == customer_user.email
    customer_user.refresh_from_db(fields=("is_confirmed",))

    # Should have properly confirmed the account
    assert customer_user.is_confirmed is True
    match_orders_with_new_user_mock.assert_called_once_with(customer_user)
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    mocked_account_confirmed.assert_called_once_with(customer_user)


@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
@patch("saleor.plugins.manager.PluginsManager.account_confirmed")
def test_account_confirmation_rejects_disabled_accounts(
    mocked_account_confirmed,
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    api_client,
    customer_user,
    throttling_disabled,
):
    """Ensure a user with `is_active=False` cannot confirm their account.

    A disabled account shouldn't be able to interact with our API, thus we
    are ensuring `is_active=False` results to the request being rejected.
    """

    # given
    customer_user.is_confirmed = False
    customer_user.is_active = False
    customer_user.save(update_fields=("is_confirmed", "is_active"))
    token = account_confirm_token_generator.make_token(customer_user)
    variables = {
        "email": customer_user.email,
        "token": token,
        "password": "password",
    }

    # when
    response = get_graphql_content(
        api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    )

    # then
    data = response["data"]["confirmAccount"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "token"
    assert errors[0]["code"] == AccountErrorCode.INVALID.name
    assert data["user"] is None
    customer_user.refresh_from_db(fields=("is_confirmed",))

    # Shouldn't have activated the account
    assert customer_user.is_confirmed is False
    match_orders_with_new_user_mock.assert_not_called()
    assign_gift_cards_mock.assert_not_called()
    mocked_account_confirmed.assert_not_called()

    # Sanity check: should work when is_active=True
    customer_user.is_active = True
    customer_user.save(update_fields=("is_active",))
    response = get_graphql_content(
        api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    )
    assert not response["data"]["confirmAccount"]["errors"], (
        "should have accepted the token"
    )
    customer_user.refresh_from_db(fields=("is_confirmed",))
    assert customer_user.is_confirmed is True, "shouldh have activated the account"
    match_orders_with_new_user_mock.assert_called_once_with(customer_user)
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    mocked_account_confirmed.assert_called_once_with(customer_user)


@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
@patch("saleor.plugins.manager.PluginsManager.account_confirmed")
def test_account_confirmation_rejects_already_confirmed(
    mocked_account_confirmed,
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    api_client,
    customer_user,
    throttling_disabled,
):
    """Ensure a user with `is_confirmed=True` cannot confirm their account.

    An already confirmed account shouldn't be able to confirm their account
    again; this is invalid operation therefore should be rejected.
    """

    # given
    assert customer_user.is_confirmed is True
    token = account_confirm_token_generator.make_token(customer_user)
    variables = {
        "email": customer_user.email,
        "token": token,
        "password": "password",
    }

    # when
    response = get_graphql_content(
        api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    )

    # then
    data = response["data"]["confirmAccount"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "token"
    assert errors[0]["code"] == AccountErrorCode.INVALID.name
    assert data["user"] is None
    customer_user.refresh_from_db(fields=("is_confirmed",))
    assert customer_user.is_confirmed is True, "shouldn't have changed"

    # Shouldn't have performed post-confirm actions
    match_orders_with_new_user_mock.assert_not_called()
    assign_gift_cards_mock.assert_not_called()
    mocked_account_confirmed.assert_not_called()

    # Sanity check: should work when is_confirmed=False
    customer_user.is_confirmed = False
    customer_user.save(update_fields=("is_confirmed",))
    response = get_graphql_content(
        api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    )
    assert not response["data"]["confirmAccount"]["errors"], (
        "should have accepted the token"
    )
    customer_user.refresh_from_db(fields=("is_confirmed",))
    assert customer_user.is_confirmed is True, "should have activated the account"
    match_orders_with_new_user_mock.assert_called_once_with(customer_user)
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    mocked_account_confirmed.assert_called_once_with(customer_user)
