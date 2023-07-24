from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
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
        "token": default_token_generator.make_token(customer_user),
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
        "token": default_token_generator.make_token(customer_user),
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(CONFIRM_ACCOUNT_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["confirmAccount"]["errors"][0]["field"] == "email"
    assert (
        content["data"]["confirmAccount"]["errors"][0]["code"]
        == AccountErrorCode.NOT_FOUND.name
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
