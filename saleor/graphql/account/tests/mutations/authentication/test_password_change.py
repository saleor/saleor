from ......account import events as account_events
from ......account.error_codes import AccountErrorCode
from ......site import PasswordLoginMode
from .....tests.utils import get_graphql_content

CHANGE_PASSWORD_MUTATION = """
    mutation PasswordChange($oldPassword: String, $newPassword: String!) {
        passwordChange(oldPassword: $oldPassword, newPassword: $newPassword) {
            errors {
                field
                message
                code
            }
            user {
                email
            }
        }
    }
"""


def test_password_change(user_api_client):
    customer_user = user_api_client.user
    new_password = "spanish-inquisition"

    variables = {"oldPassword": "password", "newPassword": new_password}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["passwordChange"]
    assert not data["errors"]
    assert data["user"]["email"] == customer_user.email

    customer_user.refresh_from_db()
    assert customer_user.check_password(new_password)

    password_change_event = account_events.CustomerEvent.objects.get()
    assert password_change_event.type == account_events.CustomerEvents.PASSWORD_CHANGED
    assert password_change_event.user == customer_user


def test_password_change_incorrect_old_password(user_api_client):
    customer_user = user_api_client.user
    variables = {"oldPassword": "incorrect", "newPassword": ""}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["passwordChange"]
    customer_user.refresh_from_db()
    assert customer_user.check_password("password")
    assert data["errors"]
    assert data["errors"][0]["field"] == "oldPassword"


def test_password_change_invalid_new_password(user_api_client, settings):
    settings.AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {"min_length": 5},
        },
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    customer_user = user_api_client.user
    variables = {"oldPassword": "password", "newPassword": "1234"}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["passwordChange"]["errors"]
    customer_user.refresh_from_db()
    assert customer_user.check_password("password")
    assert len(errors) == 2
    assert errors[1]["field"] == "newPassword"
    assert (
        errors[0]["message"]
        == "This password is too short. It must contain at least 5 characters."
    )
    assert errors[1]["field"] == "newPassword"
    assert errors[1]["message"] == "This password is entirely numeric."


def test_password_change_user_unusable_password_fails_if_old_password_is_set(
    user_api_client,
):
    customer_user = user_api_client.user
    customer_user.set_unusable_password()
    customer_user.save()

    new_password = "spanish-inquisition"

    variables = {"oldPassword": "password", "newPassword": new_password}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["passwordChange"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "oldPassword"

    customer_user.refresh_from_db()
    assert not customer_user.has_usable_password()


def test_password_change_user_unusable_password_if_old_password_is_omitted(
    user_api_client,
):
    customer_user = user_api_client.user
    customer_user.set_unusable_password()
    customer_user.save()

    new_password = "spanish-inquisition"

    variables = {"oldPassword": None, "newPassword": new_password}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["passwordChange"]
    assert not data["errors"]
    assert data["user"]["email"] == customer_user.email

    customer_user.refresh_from_db()
    assert customer_user.check_password(new_password)

    password_change_event = account_events.CustomerEvent.objects.get()
    assert password_change_event.type == account_events.CustomerEvents.PASSWORD_CHANGED
    assert password_change_event.user == customer_user


def test_password_change_user_usable_password_fails_if_old_password_is_omitted(
    user_api_client,
):
    customer_user = user_api_client.user

    new_password = "spanish-inquisition"

    variables = {"newPassword": new_password}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["passwordChange"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "oldPassword"

    customer_user.refresh_from_db()
    assert customer_user.has_usable_password()
    assert not customer_user.check_password(new_password)


def test_password_change_disabled_password_login(user_api_client, site_settings):
    # given
    site_settings.password_login_mode = PasswordLoginMode.DISABLED
    site_settings.save(update_fields=["password_login_mode"])
    variables = {"oldPassword": "password", "newPassword": "new-password"}

    # when
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["passwordChange"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["code"] == AccountErrorCode.DISABLED_AUTHENTICATION_METHOD.name
    assert error["field"] == "email"

    user_api_client.user.refresh_from_db()
    assert user_api_client.user.check_password("password")
