from datetime import datetime, timedelta, timezone

import graphene
from django.urls import reverse
from freezegun import freeze_time

from .....account.error_codes import AccountErrorCode
from .....core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TYPE,
    create_refresh_token,
    jwt_decode,
)
from .....core.utils import build_absolute_uri
from ....tests.utils import get_graphql_content
from ...mutations.authentication import _get_new_csrf_token

MUTATION_CREATE_TOKEN = """
    mutation tokenCreate($email: String!, $password: String!, $audience: String){
        tokenCreate(email: $email, password: $password, audience: $audience) {
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
            errors {
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
    assert content["data"]["tokenCreate"]["errors"] == []

    token = data["token"]
    refreshToken = data["refreshToken"]

    payload = jwt_decode(token)
    assert payload["email"] == customer_user.email
    assert payload["user_id"] == graphene.Node.to_global_id("User", customer_user.id)
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + settings.JWT_TTL_ACCESS
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_ACCESS_TYPE

    payload = jwt_decode(refreshToken)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + settings.JWT_TTL_REFRESH
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_REFRESH_TYPE
    assert payload["token"] == customer_user.jwt_token_key
    assert payload["iss"] == build_absolute_uri(reverse("api"))


@freeze_time("2020-03-18 12:00:00")
def test_create_token_with_audience(api_client, customer_user, settings):
    audience = "dashboard"
    variables = {
        "email": customer_user.email,
        "password": customer_user._password,
        "audience": audience,
    }
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenCreate"]

    user_email = data["user"]["email"]
    assert customer_user.email == user_email
    assert content["data"]["tokenCreate"]["errors"] == []

    token = data["token"]
    refreshToken = data["refreshToken"]

    payload = jwt_decode(token)
    assert payload["email"] == customer_user.email
    assert payload["user_id"] == graphene.Node.to_global_id("User", customer_user.id)
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + settings.JWT_TTL_ACCESS
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_ACCESS_TYPE
    assert payload["aud"] == f"custom:{audience}"

    payload = jwt_decode(refreshToken)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + settings.JWT_TTL_REFRESH
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_REFRESH_TYPE
    assert payload["token"] == customer_user.jwt_token_key
    assert payload["aud"] == f"custom:{audience}"


@freeze_time("2020-03-18 12:00:00")
def test_create_token_sets_cookie(api_client, customer_user, settings, monkeypatch):
    csrf_token = _get_new_csrf_token()
    monkeypatch.setattr(
        "saleor.graphql.account.mutations.authentication._get_new_csrf_token",
        lambda: csrf_token,
    )
    variables = {"email": customer_user.email, "password": customer_user._password}
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)

    expected_refresh_token = create_refresh_token(
        customer_user, {"csrfToken": csrf_token}
    )
    refresh_token = response.cookies["refreshToken"]
    assert refresh_token.value == expected_refresh_token
    expected_expires = datetime.utcnow() + settings.JWT_TTL_REFRESH
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
    response_error = content["data"]["tokenCreate"]["errors"][0]
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


def test_create_token_invalid_email(api_client, customer_user):
    variables = {"email": "wrongemail", "password": "wrongpassword"}
    expected_error_code = AccountErrorCode.INVALID_CREDENTIALS.value.upper()
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)
    response_error = content["data"]["tokenCreate"]["errors"][0]
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


def test_create_token_unconfirmed_email(api_client, customer_user):
    # given
    variables = {"email": customer_user.email, "password": customer_user._password}
    customer_user.is_active = False
    customer_user.save()
    expected_error_code = AccountErrorCode.ACCOUNT_NOT_CONFIRMED.value.upper()

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)
    response_error = content["data"]["tokenCreate"]["errors"][0]

    # then
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


def test_create_token_deactivated_user(api_client, customer_user):
    # given
    variables = {"email": customer_user.email, "password": customer_user._password}
    customer_user.is_active = False
    customer_user.last_login = datetime(2020, 3, 18, tzinfo=timezone.utc)
    customer_user.save()
    expected_error_code = AccountErrorCode.INACTIVE.value.upper()

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)
    response_error = content["data"]["tokenCreate"]["errors"][0]

    # then
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


@freeze_time("2020-03-18 12:00:00")
def test_create_token_active_user_logged_before(api_client, customer_user, settings):
    variables = {"email": customer_user.email, "password": customer_user._password}
    customer_user.last_login = datetime(2020, 3, 18, tzinfo=timezone.utc)
    customer_user.save()
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenCreate"]

    user_email = data["user"]["email"]
    assert customer_user.email == user_email
    assert content["data"]["tokenCreate"]["errors"] == []

    token = data["token"]
    refreshToken = data["refreshToken"]

    payload = jwt_decode(token)
    assert payload["email"] == customer_user.email
    assert payload["user_id"] == graphene.Node.to_global_id("User", customer_user.id)
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + settings.JWT_TTL_ACCESS
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_ACCESS_TYPE

    payload = jwt_decode(refreshToken)
    assert payload["email"] == customer_user.email
    assert datetime.fromtimestamp(payload["iat"]) == datetime.utcnow()
    expected_expiration_datetime = datetime.utcnow() + settings.JWT_TTL_REFRESH
    assert datetime.fromtimestamp(payload["exp"]) == expected_expiration_datetime
    assert payload["type"] == JWT_REFRESH_TYPE
    assert payload["token"] == customer_user.jwt_token_key
    assert payload["iss"] == build_absolute_uri(reverse("api"))
