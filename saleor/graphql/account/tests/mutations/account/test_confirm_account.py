from unittest.mock import patch

from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......core.tokens import (
    account_confirm_token_generator,
    legacy_account_confirm_token_generator,
    password_reset_token_generator,
)
from .....tests.utils import get_graphql_content

CONFIRM_ACCOUNT_MUTATION = """
    mutation ConfirmAccount($email: String!, $token: String!) {
        confirmAccount(email: $email, token: $token) {
            errors {
                field
                code
            }
            user {
                id
                email
            }
        }
    }
"""


@freeze_time("2018-05-31 12:00:01")
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.assign_user_gift_cards"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_account.match_orders_with_new_user"
)
@patch("saleor.plugins.manager.PluginsManager.account_confirmed")
def test_account_confirmation(
    match_orders_with_new_user_mock,
    assign_gift_cards_mock,
    mocked_account_confirmed,
    api_client,
    customer_user,
    channel_USD,
):
    customer_user.is_confirmed = False
    customer_user.save()

    variables = {
        "email": customer_user.email,
        "token": account_confirm_token_generator.make_token(customer_user),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    content = get_graphql_content(response)
    assert not content["data"]["confirmAccount"]["errors"]
    assert content["data"]["confirmAccount"]["user"]["email"] == customer_user.email
    customer_user.refresh_from_db()
    match_orders_with_new_user_mock.assert_called_once_with(customer_user)
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    assert customer_user.is_confirmed is True
    mocked_account_confirmed.assert_called_once_with(customer_user)


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
):
    """Ensure old tokens before adding scopes still work properly."""

    # given
    customer_user.is_confirmed = False
    customer_user.save(update_fields=["is_confirmed"])
    token = legacy_account_confirm_token_generator.make_token(customer_user)
    variables = {
        "email": customer_user.email,
        "token": token,
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
    assert customer_user.is_confirmed is True, "shouldh have activated the account"
    match_orders_with_new_user_mock.assert_called_once_with(customer_user)
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    mocked_account_confirmed.assert_called_once_with(customer_user)
