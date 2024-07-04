from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import graphene
import pytz
from django.urls import reverse
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.throttling import (
    get_cache_key_blocked_ip,
    get_cache_key_failed_ip,
    get_cache_key_failed_ip_with_user,
    get_delay_time,
)
from ......core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TYPE,
    create_refresh_token,
    jwt_decode,
)
from ......core.utils import build_absolute_uri
from .....tests.utils import get_graphql_content
from ....mutations.authentication.utils import _get_new_csrf_token

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
@patch("saleor.account.throttling.cache")
def test_create_token(_mocked_cache, api_client, customer_user, settings):
    # given
    variables = {"email": customer_user.email, "password": customer_user._password}

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
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
@patch("saleor.account.throttling.cache")
def test_create_token_with_audience(_mocked_cache, api_client, customer_user, settings):
    # given
    audience = "dashboard"
    variables = {
        "email": customer_user.email,
        "password": customer_user._password,
        "audience": audience,
    }

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
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
@patch("saleor.account.throttling.cache")
def test_create_token_sets_cookie(
    _mocked_cache, api_client, customer_user, settings, monkeypatch
):
    # given
    csrf_token = _get_new_csrf_token()
    monkeypatch.setattr(
        "saleor.graphql.account.mutations.authentication.create_token._get_new_csrf_token",
        lambda: csrf_token,
    )
    variables = {"email": customer_user.email, "password": customer_user._password}

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)

    # then
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


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_create_token_invalid_password(_mocked_cache, api_client, customer_user):
    # given
    variables = {"email": customer_user.email, "password": "wrongpassword"}
    expected_error_code = AccountErrorCode.INVALID_CREDENTIALS.value.upper()

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
    response_error = content["data"]["tokenCreate"]["errors"][0]
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_create_token_invalid_email(_mocked_cache, api_client, customer_user):
    # given
    variables = {"email": "wrongemail", "password": "wrongpassword"}
    expected_error_code = AccountErrorCode.INVALID_CREDENTIALS.value.upper()

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
    response_error = content["data"]["tokenCreate"]["errors"][0]
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_create_token_unconfirmed_email(_mocked_cache, api_client, customer_user):
    # given
    variables = {"email": customer_user.email, "password": customer_user._password}
    customer_user.is_confirmed = False
    customer_user.save()
    expected_error_code = AccountErrorCode.ACCOUNT_NOT_CONFIRMED.value.upper()

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)
    response_error = content["data"]["tokenCreate"]["errors"][0]

    # then
    assert response_error["code"] == expected_error_code
    assert response_error["field"] == "email"


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.account.throttling.cache")
def test_create_token_unconfirmed_user_unconfirmed_login_enabled(
    _mocked_cache, api_client, customer_user, settings, site_settings
):
    # given
    variables = {"email": customer_user.email, "password": customer_user._password}
    site_settings.allow_login_without_confirmation = True
    site_settings.save()
    customer_user.is_confirmed = False
    customer_user.save()

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
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
@patch("saleor.account.throttling.cache")
def test_create_token_deactivated_user(_mocked_cache, api_client, customer_user):
    # given
    variables = {"email": customer_user.email, "password": customer_user._password}
    customer_user.is_active = False
    customer_user.is_confirmed = True
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
@patch("saleor.account.throttling.cache")
def test_create_token_active_user_logged_before(
    _mocked_cache, api_client, customer_user, settings
):
    # given
    variables = {"email": customer_user.email, "password": customer_user._password}
    customer_user.last_login = datetime(2020, 3, 18, tzinfo=timezone.utc)
    customer_user.save()

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
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
@patch("saleor.account.throttling.cache")
def test_create_token_email_case_insensitive(
    _mocked_cache, api_client, customer_user, settings
):
    # given
    variables = {
        "email": customer_user.email.upper(),
        "password": customer_user._password,
    }

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["tokenCreate"]
    assert customer_user.email == data["user"]["email"]
    assert not data["errors"]
    assert data["token"]


@freeze_time("2020-03-18 12:00:00")
def test_create_token_do_not_update_last_login_when_in_threshold(
    api_client, customer_user, settings
):
    # given
    customer_password = customer_user._password
    customer_user.last_login = datetime.now(tz=pytz.UTC)
    customer_user.save()
    expected_last_login = customer_user.last_login
    expected_updated_at = customer_user.updated_at
    variables = {"email": customer_user.email, "password": customer_password}
    time_in_threshold = datetime.now(tz=pytz.UTC) + timedelta(
        seconds=settings.TOKEN_UPDATE_LAST_LOGIN_THRESHOLD - 1
    )

    # when
    with freeze_time(time_in_threshold):
        response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)

    # then
    get_graphql_content(response)
    customer_user.refresh_from_db()
    assert customer_user.updated_at == expected_updated_at
    assert customer_user.last_login == expected_last_login


@freeze_time("2020-03-18 12:00:00")
def test_create_token_do_update_last_login_when_out_of_threshold(
    api_client, customer_user, settings
):
    # given
    customer_password = customer_user._password
    customer_user.last_login = datetime.now(tz=pytz.UTC)
    customer_user.save()
    previous_last_login = customer_user.last_login
    previous_updated_at = customer_user.updated_at

    variables = {"email": customer_user.email, "password": customer_password}
    time_in_threshold = datetime.now(tz=pytz.UTC) + timedelta(
        seconds=settings.TOKEN_UPDATE_LAST_LOGIN_THRESHOLD + 1
    )

    # when
    with freeze_time(time_in_threshold):
        response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)

    # then
    get_graphql_content(response)
    customer_user.refresh_from_db()
    assert customer_user.updated_at != previous_updated_at
    assert customer_user.last_login != previous_last_login
    assert customer_user.updated_at == time_in_threshold
    assert customer_user.last_login == time_in_threshold


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.account.throttling.get_client_ip")
@patch("saleor.account.throttling.cache")
def test_create_token_throttling_login_attempt_delay(
    mocked_cache, mocked_get_ip, api_client, customer_user, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = datetime.utcnow()

    variables = {"email": customer_user.email, "password": "incorrect-password"}

    ip = "123.123.123.123"
    mocked_get_ip.return_value = ip

    # imitate cache state after a couple of failed login attempts
    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    ip_attempts_count = 21
    ip_user_attempts_count = 5
    mocked_cache.set(ip_key, ip_attempts_count, timeout=100)
    mocked_cache.set(ip_user_key, ip_user_attempts_count, timeout=100)
    expected_delay = get_delay_time(ip_attempts_count + 1, ip_user_attempts_count + 1)
    next_attempt = now + timedelta(seconds=expected_delay)
    mocked_cache.set(block_key, next_attempt, timeout=100)

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["tokenCreate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.LOGIN_ATTEMPT_DELAYED.name
    assert error["field"] is None
    assert str(next_attempt) in error["message"]


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.account.throttling.get_client_ip")
@patch("saleor.account.throttling.cache")
def test_create_token_throttling_unidentified_ip_address(
    _mocked_cache, mock_get_ip, api_client, customer_user
):
    # given
    mock_get_ip.return_value = None
    variables = {
        "email": customer_user.email,
        "password": customer_user._password,
    }

    # when
    response = api_client.post_graphql(MUTATION_CREATE_TOKEN, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["tokenCreate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AccountErrorCode.UNKNOWN_IP_ADDRESS.name
    assert error["field"] is None
