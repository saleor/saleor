from datetime import datetime, timedelta

import graphene
from freezegun import freeze_time
from jwt import decode

from saleor.account.error_codes import AccountErrorCode
from saleor.core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_ALGORITHM,
    JWT_EXPIRATION_DELTA,
    JWT_REFRESH_EXPIRATION_DELTA,
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    JWT_REFRESH_TYPE,
    JWT_SECRET,
    create_access_token,
    create_refresh_token,
)
from tests.api.utils import get_graphql_content

MUTATION_CREATE_TOKEN = """
    mutation tokenCreate($email: String!, $password: String!){
        tokenCreate(email: $email, password: $password) {
            token
            refreshToken
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
def test_create_token(api_client, customer_user):
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
    expected_expiration_datetime = datetime.utcnow() + JWT_EXPIRATION_DELTA
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_ACCESS_TYPE

    payload = decode(refreshToken, JWT_SECRET, algorithms=JWT_ALGORITHM)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + JWT_REFRESH_EXPIRATION_DELTA
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_REFRESH_TYPE


@freeze_time("2020-03-18 12:00:00")
def test_create_token_sets_cookie(api_client, customer_user):
    variables = {"email": customer_user.email, "password": customer_user._password}
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)

    expected_refresh_token = create_refresh_token(customer_user)
    refresh_token = response.cookies["refreshToken"]
    assert refresh_token.value == expected_refresh_token
    expected_expires = datetime.utcnow() + JWT_REFRESH_EXPIRATION_DELTA
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


MUTATION_TOKEN_REFRESH = """
    mutation tokenRefresh($token: String){
        tokenRefresh(refreshToken: $token){
            token
            accountErrors{
              code
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_get_token_from_cookie(
    api_client, customer_user,
):
    refresh_token = create_refresh_token(customer_user)
    variables = {"token": None}
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
        == datetime.utcnow() + JWT_EXPIRATION_DELTA
    )
    assert payload["type"] == JWT_ACCESS_TYPE


@freeze_time("2020-03-18 12:00:00")
def test_refresh_token_get_token_from_input(api_client, customer_user):
    refresh_token = create_refresh_token(customer_user)
    variables = {"token": refresh_token}
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
        == datetime.utcnow() + JWT_EXPIRATION_DELTA
    )
    assert payload["type"] == JWT_ACCESS_TYPE


def test_refresh_token_get_token_missing_token(api_client, customer_user):
    variables = {"token": None}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["accountErrors"]

    token = data.get("token")
    assert not token

    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_MISSING_TOKEN.name


def test_refresh_token_when_expired(api_client, customer_user):
    with freeze_time("2018-05-31 12:00:01"):
        refresh_token = create_refresh_token(customer_user)

    variables = {"token": None}
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
    refresh_token = create_refresh_token(customer_user)

    variables = {"token": None}
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
