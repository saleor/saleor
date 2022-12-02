from datetime import datetime

from django.middleware.csrf import _get_new_csrf_token
from freezegun import freeze_time

from .....account.error_codes import AccountErrorCode
from .....core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    create_access_token,
    create_access_token_for_app,
    create_refresh_token,
    jwt_decode,
)
from ....tests.utils import get_graphql_content

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
