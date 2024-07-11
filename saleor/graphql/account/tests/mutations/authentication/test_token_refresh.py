from datetime import datetime, timedelta

import pytest
import pytz
from django.urls import reverse
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    create_access_token,
    create_access_token_for_app,
    create_refresh_token,
    jwt_decode,
)
from ......core.utils import build_absolute_uri
from .....tests.utils import get_graphql_content
from ....mutations.authentication.utils import _get_new_csrf_token

MUTATION_TOKEN_REFRESH = """
    mutation tokenRefresh($token: String, $csrf_token: String){
        tokenRefresh(refreshToken: $token, csrfToken: $csrf_token){
            token
            errors{
              code
              field
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_with_audience(api_client, customer_user, settings):
    csrf_token = _get_new_csrf_token()
    token_audience = "custom:dashboard"
    refresh_token = create_refresh_token(
        customer_user, {"csrfToken": csrf_token, "aud": token_audience}
    )
    variables = {"token": None, "csrf_token": csrf_token}
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    assert not errors
    token = data.get("token")
    assert token
    payload = jwt_decode(token)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    assert (
        datetime.fromtimestamp(payload["exp"])
        == datetime.utcnow() + settings.JWT_TTL_ACCESS
    )
    assert payload["type"] == JWT_ACCESS_TYPE
    assert payload["token"] == customer_user.jwt_token_key
    assert payload["aud"] == token_audience
    customer_user.refresh_from_db()
    assert customer_user.last_login
    last_login = customer_user.last_login.strftime("%Y-%m-%d %H:%M:%S")
    assert last_login == "2020-03-18 12:00:00"


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_get_token_from_cookie(api_client, customer_user, settings):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    variables = {"token": None, "csrf_token": csrf_token}
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    assert not errors
    token = data.get("token")
    assert token
    payload = jwt_decode(token)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    assert (
        datetime.fromtimestamp(payload["exp"])
        == datetime.utcnow() + settings.JWT_TTL_ACCESS
    )
    assert payload["type"] == JWT_ACCESS_TYPE
    assert payload["token"] == customer_user.jwt_token_key
    assert payload["iss"] == build_absolute_uri(reverse("api"))


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_get_token_from_input(api_client, customer_user, settings):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    variables = {"token": refresh_token, "csrf_token": None}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    assert not errors
    token = data.get("token")
    assert token
    payload = jwt_decode(token)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    assert (
        datetime.fromtimestamp(payload["exp"])
        == datetime.utcnow() + settings.JWT_TTL_ACCESS
    )
    assert payload["type"] == JWT_ACCESS_TYPE


def test_refresh_token_get_token_missing_token(api_client, customer_user):
    variables = {"token": None, "csrf_token": "token"}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_MISSING_TOKEN.name


def test_access_token_used_as_a_refresh_token(api_client, customer_user):
    csrf_token = _get_new_csrf_token()
    access_token = create_access_token(customer_user, {"csrfToken": csrf_token})

    variables = {"token": access_token, "csrf_token": csrf_token}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name


def test_access_app_token_used_as_a_refresh_token(api_client, app, customer_user):
    csrf_token = _get_new_csrf_token()
    access_app_token = create_access_token_for_app(app, customer_user)

    variables = {"token": access_app_token, "csrf_token": csrf_token}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name


def test_refresh_token_get_token_missing_csrf_token(api_client, customer_user):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    variables = {"token": None}
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.REQUIRED.name
    assert errors[0]["field"] == "csrfToken"


def test_refresh_token_get_token_incorrect_csrf_token(api_client, customer_user):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    variables = {"token": None, "csrf_token": "csrf_token"}
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_CSRF_TOKEN.name


def test_refresh_token_when_expired(api_client, customer_user):
    with freeze_time("2018-05-31 12:00:01"):
        csrf_token = _get_new_csrf_token()
        refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})

    variables = {"token": None, "csrf_token": csrf_token}
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True

    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)

    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_SIGNATURE_EXPIRED.name


def test_refresh_token_when_incorrect_token(api_client, customer_user):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})

    variables = {"token": None, "csrf_token": csrf_token}
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token + "wrong-token"
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True

    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)

    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_DECODE_ERROR.name


def test_refresh_token_when_user_deactivated_token(api_client, customer_user):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    customer_user.jwt_token_key = "new_key"
    customer_user.save()
    variables = {"token": None, "csrf_token": csrf_token}
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True

    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["errors"]

    assert not data["token"]
    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name


@pytest.mark.parametrize("token", ["incorrect-token", ""])
def test_refresh_token_incorrect_token_provided(api_client, customer_user, token):
    # given
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True

    variables = {"token": token, "csrf_token": csrf_token}

    # when
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["tokenRefresh"]
    errors = data["errors"]
    assert not data.get("token")
    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_DECODE_ERROR.name


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_do_not_update_last_login_when_in_threshold(
    api_client, customer_user, settings
):
    # given
    csrf_token = _get_new_csrf_token()
    token_audience = "custom:dashboard"
    refresh_token = create_refresh_token(
        customer_user, {"csrfToken": csrf_token, "aud": token_audience}
    )
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True

    customer_user.last_login = datetime.now(tz=pytz.UTC)
    customer_user.save()

    expected_last_login = customer_user.last_login
    expected_updated_at = customer_user.updated_at

    variables = {"token": None, "csrf_token": csrf_token}

    time_in_threshold = datetime.now(tz=pytz.UTC) + timedelta(
        seconds=settings.TOKEN_UPDATE_LAST_LOGIN_THRESHOLD - 1
    )

    # when
    with freeze_time(time_in_threshold):
        response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)

    # then
    get_graphql_content(response)
    customer_user.refresh_from_db()
    assert customer_user.updated_at == expected_updated_at
    assert customer_user.last_login == expected_last_login


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_do_update_last_login_when_out_of_threshold(
    api_client, customer_user, settings
):
    # given
    csrf_token = _get_new_csrf_token()
    token_audience = "custom:dashboard"
    refresh_token = create_refresh_token(
        customer_user, {"csrfToken": csrf_token, "aud": token_audience}
    )
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME] = refresh_token
    api_client.cookies[JWT_REFRESH_TOKEN_COOKIE_NAME]["httponly"] = True

    customer_user.last_login = datetime.now(tz=pytz.UTC)
    customer_user.save()

    previous_last_login = customer_user.last_login
    previous_updated_at = customer_user.updated_at

    variables = {"token": None, "csrf_token": csrf_token}

    time_in_threshold = datetime.now(tz=pytz.UTC) + timedelta(
        seconds=settings.TOKEN_UPDATE_LAST_LOGIN_THRESHOLD + 1
    )

    # when
    with freeze_time(time_in_threshold):
        response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)

    # then
    get_graphql_content(response)
    customer_user.refresh_from_db()
    assert customer_user.updated_at != previous_updated_at
    assert customer_user.last_login != previous_last_login
    assert customer_user.updated_at == time_in_threshold
    assert customer_user.last_login == time_in_threshold
