from unittest.mock import patch

from freezegun import freeze_time

from ......account import events as account_events
from ......account.error_codes import AccountErrorCode
from ......core.tokens import token_generator
from .....core.utils import str_to_enum
from .....tests.utils import get_graphql_content
from ....mutations.base import INVALID_TOKEN

SET_PASSWORD_MUTATION = """
    mutation SetPassword($email: String!, $token: String!, $password: String!) {
        setPassword(email: $email, token: $token, password: $password) {
            errors {
                field
                message
            }
            errors {
                field
                message
                code
            }
            user {
                id
            }
            token
            refreshToken
        }
    }
"""


@freeze_time("2018-05-31 12:00:01")
def test_set_password(user_api_client, customer_user):
    token = token_generator.make_token(customer_user)
    password = "spanish-inquisition"

    variables = {"email": customer_user.email, "password": password, "token": token}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["setPassword"]
    assert data["user"]["id"]
    assert data["token"]

    customer_user.refresh_from_db()
    assert customer_user.check_password(password)

    password_resent_event = account_events.CustomerEvent.objects.get()
    assert password_resent_event.type == account_events.CustomerEvents.PASSWORD_RESET
    assert password_resent_event.user == customer_user


@freeze_time("2018-05-31 12:00:01")
@patch(
    "saleor.graphql.account.mutations.authentication.set_password.match_orders_with_new_user"
)
def test_set_password_confirm_user_and_match_orders(
    match_orders_with_new_user_mock, user_api_client, customer_user
):
    # given
    customer_user.is_confirmed = False
    customer_user.save(update_fields=["is_confirmed"])

    token = token_generator.make_token(customer_user)
    password = "spanish-inquisition"

    variables = {"email": customer_user.email, "password": password, "token": token}

    # when
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["setPassword"]
    assert data["user"]["id"]
    assert data["token"]

    customer_user.refresh_from_db()
    assert customer_user.check_password(password)

    password_resent_event = account_events.CustomerEvent.objects.get()
    assert password_resent_event.type == account_events.CustomerEvents.PASSWORD_RESET
    assert password_resent_event.user == customer_user
    assert customer_user.is_confirmed
    match_orders_with_new_user_mock.assert_called_once_with(customer_user)


def test_set_password_invalid_token(user_api_client, customer_user):
    variables = {"email": customer_user.email, "password": "pass", "token": "token"}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["setPassword"]["errors"]
    assert errors[0]["message"] == INVALID_TOKEN

    account_errors = content["data"]["setPassword"]["errors"]
    assert account_errors[0]["message"] == INVALID_TOKEN
    assert account_errors[0]["code"] == AccountErrorCode.INVALID.name


def test_set_password_invalid_email(user_api_client):
    variables = {"email": "fake@example.com", "password": "pass", "token": "token"}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["setPassword"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "token"

    account_errors = content["data"]["setPassword"]["errors"]
    assert len(account_errors) == 1
    assert account_errors[0]["field"] == "token"
    assert account_errors[0]["code"] == AccountErrorCode.INVALID.name


@freeze_time("2018-05-31 12:00:01")
def test_set_password_invalid_password(user_api_client, customer_user, settings):
    settings.AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {"min_length": 5},
        },
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    token = token_generator.make_token(customer_user)
    variables = {"email": customer_user.email, "password": "1234", "token": token}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["setPassword"]["errors"]
    assert len(errors) == 2
    assert (
        errors[0]["message"]
        == "This password is too short. It must contain at least 5 characters."
    )
    assert errors[1]["message"] == "This password is entirely numeric."

    account_errors = content["data"]["setPassword"]["errors"]
    assert account_errors[0]["code"] == str_to_enum("password_too_short")
    assert account_errors[1]["code"] == str_to_enum("password_entirely_numeric")
