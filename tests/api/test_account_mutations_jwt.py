from datetime import datetime, timedelta

import graphene
from django.middleware.csrf import _get_new_csrf_token
from freezegun import freeze_time
from jwt import decode

from saleor.account.error_codes import AccountErrorCode
from saleor.core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    JWT_REFRESH_TYPE,
    JWT_SECRET,
    create_access_token,
    create_refresh_token,
    jwt_decode,
)
from tests.api.utils import get_graphql_content

MUTATION_CREATE_TOKEN = """
    mutation tokenCreate($email: String!, $password: String!){
        tokenCreate(email: $email, password: $password) {
            token
            refreshToken
            csrfToken
            user {
                email
            }
            errors {
                field
                message
            }
            accountErrors {
                field
                message
                code
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
def test_create_token(api_client, customer_user, settings):
    variables = {"email": customer_user.email, "password": customer_user._password}
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenCreate"]

    user_email = data["user"]["email"]
    assert customer_user.email == user_email
    assert content["data"]["tokenCreate"]["accountErrors"] == []

    token = data["token"]
    refreshToken = data["refreshToken"]

    payload = decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
    assert payload["email"] == customer_user.email
    assert payload["user_id"] == graphene.Node.to_global_id("User", customer_user.id)
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + settings.JWT_EXPIRATION_DELTA
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_ACCESS_TYPE

    payload = decode(refreshToken, JWT_SECRET, algorithms=JWT_ALGORITHM)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = (
        datetime.utcnow() + settings.JWT_REFRESH_EXPIRATION_DELTA
    )
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_REFRESH_TYPE
    assert payload["token"] == customer_user.jwt_token_key


@freeze_time("2020-03-18 12:00:00")
def test_create_token_sets_cookie(api_client, customer_user, settings, monkeypatch):
    csrf_token = _get_new_csrf_token()
    monkeypatch.setattr(
        "saleor.graphql.account.mutations.jwt._get_new_csrf_token", lambda: csrf_token
    )
    variables = {"email": customer_user.email, "password": customer_user._password}
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)

    expected_refresh_token = create_refresh_token(
        customer_user, {"csrfToken": csrf_token}
    )
    refresh_token = response.cookies["refreshToken"]
    assert refresh_token.value == expected_refresh_token
    expected_expires = datetime.utcnow() + settings.JWT_REFRESH_EXPIRATION_DELTA
    expected_expires += timedelta(seconds=1)
    expires = datetime.strptime(refresh_token["expires"], "%a, %d %b %Y  %H:%M:%S %Z")
    assert expires == expected_expires
    assert refresh_token["httponly"]
    assert refresh_token["secure"]


def test_create_token_invalid_password(api_client, customer_user):
    variables = {"email": customer_user.email, "password": "wrongpassword"}
    expected_error_code = AccountErrorCode.INVALID_CREDENTIALS.value.upper()
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)
    response_error = content["data"]["tokenCreate"]["accountErrors"][0]
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


def test_create_token_invalid_email(api_client, customer_user):
    variables = {"email": "wrongemail", "password": "wrongpassword"}
    expected_error_code = AccountErrorCode.INVALID_CREDENTIALS.value.upper()
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)
    response_error = content["data"]["tokenCreate"]["accountErrors"][0]
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


MUTATION_TOKEN_VERIFY = """
    mutation tokenVerify($token: String!){
        tokenVerify(token: $token){
            isValid
            user{
              email
            }
            accountErrors{
              code
            }
        }
    }
"""


def test_verify_token(api_client, customer_user):
    variables = {"token": create_access_token(customer_user)}
    response = api_client.post_graphql(MUTATION_TOKEN_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["tokenVerify"]
    assert data["isValid"]
    user_email = content["data"]["tokenVerify"]["user"]["email"]
    assert customer_user.email == user_email


def test_verify_token_incorrect_token(api_client):
    variables = {"token": "incorrect_token"}
    response = api_client.post_graphql(MUTATION_TOKEN_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["tokenVerify"]
    errors = data["accountErrors"]
    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_DECODE_ERROR.name
    assert not data["isValid"]
    assert not data["user"]


def test_verify_token_invalidated_by_user(api_client, customer_user):
    variables = {"token": create_access_token(customer_user)}
    customer_user.jwt_token_key = "new token"
    customer_user.save()
    response = api_client.post_graphql(MUTATION_TOKEN_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["tokenVerify"]
    errors = data["accountErrors"]

    assert not data["isValid"]
    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name


MUTATION_TOKEN_REFRESH = """
    mutation tokenRefresh($token: String, $csrf_token: String!){
        tokenRefresh(refreshToken: $token, csrfToken: $csrf_token){
            token
            accountErrors{
              code
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
    errors = data["accountErrors"]

    assert not errors
    token = data.get("token")
    assert token
    payload = decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    assert (
        datetime.fromtimestamp(payload["exp"])
        == datetime.utcnow() + settings.JWT_EXPIRATION_DELTA
    )
    assert payload["type"] == JWT_ACCESS_TYPE
    assert payload["token"] == customer_user.jwt_token_key


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_get_token_from_input(api_client, customer_user, settings):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    variables = {"token": refresh_token, "csrf_token": csrf_token}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["accountErrors"]

    assert not errors
    token = data.get("token")
    assert token
    payload = decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    assert (
        datetime.fromtimestamp(payload["exp"])
        == datetime.utcnow() + settings.JWT_EXPIRATION_DELTA
    )
    assert payload["type"] == JWT_ACCESS_TYPE


def test_refresh_token_get_token_missing_token(api_client, customer_user):
    variables = {"token": None, "csrf_token": "token"}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["accountErrors"]

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
    errors = data["accountErrors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name


def test_refresh_token_get_token_incorrect_csrf_token(api_client, customer_user):
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    variables = {"token": refresh_token, "csrf_token": "csrf_token"}

    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["accountErrors"]

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
    errors = data["accountErrors"]

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
    errors = data["accountErrors"]

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
    errors = data["accountErrors"]

    assert not data["token"]
    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name


MUTATION_DEACTIVATE_ALL_USER_TOKENS = """
mutation{
  tokensDeactivateAll{
    accountErrors{
      field
      message
      code
    }
  }
}

"""


@freeze_time("2020-03-18 12:00:00")
def test_deactivate_all_user_tokens(customer_user, user_api_client):
    token = create_access_token(customer_user)
    jwt_key = customer_user.jwt_token_key

    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})

    user_api_client.token = token
    user_api_client.post_graphql(MUTATION_DEACTIVATE_ALL_USER_TOKENS)
    customer_user.refresh_from_db()

    new_token = create_access_token(customer_user)
    new_refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    # the mutation changes the parameter of jwt token, which confirms if jwt token is
    # valid or not
    assert jwt_decode(token)["token"] != jwt_decode(new_token)["token"]
    assert jwt_decode(refresh_token)["token"] != jwt_decode(new_refresh_token)["token"]
    assert jwt_key != customer_user.jwt_token_key


def test_deactivate_all_user_tokens_access_token(user_api_client, customer_user):
    token = create_access_token(customer_user)
    user_api_client.token = token
    response = user_api_client.post_graphql(MUTATION_DEACTIVATE_ALL_USER_TOKENS)
    content = get_graphql_content(response)

    errors = content["data"]["tokensDeactivateAll"]["accountErrors"]
    assert not errors

    query = "{me { id }}"
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["me"] is None


def test_deactivate_all_user_token_refresh_token(
    api_client, user_api_client, customer_user
):
    user_api_client.token = create_access_token(customer_user)
    create_refresh_token(customer_user)
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})

    response = user_api_client.post_graphql(MUTATION_DEACTIVATE_ALL_USER_TOKENS)
    content = get_graphql_content(response)
    errors = content["data"]["tokensDeactivateAll"]["accountErrors"]
    assert not errors

    variables = {"token": refresh_token, "csrf_token": csrf_token}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["accountErrors"]

    assert data["token"] is None
    assert len(errors) == 1

    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name
