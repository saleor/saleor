import json
import time
import warnings
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, Mock

import pytest
import pytz
import requests
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware
from freezegun import freeze_time
from requests import Response

from ....account.models import User
from ....core.jwt import (
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ..exceptions import AuthenticationError
from ..utils import (
    JWKS_CACHE_TIME,
    JWKS_KEY,
    create_jwt_refresh_token,
    create_jwt_token,
    create_tokens_from_oauth_payload,
    fetch_jwks,
    get_or_create_user_from_payload,
    get_saleor_permission_names,
    get_saleor_permissions_qs_from_scope,
    get_user_from_token,
    get_user_info,
    validate_refresh_token,
)


@pytest.mark.parametrize(
    "error",
    [
        json.JSONDecodeError(msg="", doc="", pos=0),
        requests.exceptions.RequestException(),
    ],
)
def test_fetch_jwks_raises_error(monkeypatch, error):
    mocked_get = Mock()
    mocked_get.side_effect = error
    jwks_url = "http://localhost:3000/"
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.requests.get", mocked_get)

    with pytest.raises(AuthenticationError):
        fetch_jwks(jwks_url)


@pytest.mark.vcr
@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
def test_fetch_jwks(mocked_cache_set):
    jwks_url = "https://saleor.io/.well-known/jwks.json"
    keys = fetch_jwks(jwks_url)
    assert len(keys) == 2
    mocked_cache_set.assert_called_once_with(JWKS_KEY, keys, JWKS_CACHE_TIME)


def test_get_or_create_user_from_token_missing_email(id_payload):
    del id_payload["email"]
    with pytest.raises(AuthenticationError):
        get_or_create_user_from_payload(id_payload, "https://saleor.io/oauth")


def test_get_or_create_user_from_token_user_not_active(id_payload, admin_user):
    admin_user.is_active = False
    admin_user.save()
    with pytest.raises(AuthenticationError):
        get_or_create_user_from_payload(id_payload, "https://saleor.io/oauth")


def test_get_user_from_token_missing_email(id_payload):
    del id_payload["email"]
    with pytest.raises(AuthenticationError):
        get_user_from_token(id_payload)


def test_get_user_from_token_missing_user(id_payload):
    User.objects.all().delete()
    with pytest.raises(AuthenticationError):
        get_user_from_token(id_payload)


def test_get_user_from_token_user_not_active(id_payload, admin_user):
    admin_user.is_active = False
    admin_user.save()
    with pytest.raises(AuthenticationError):
        get_user_from_token(id_payload)


@freeze_time("2019-03-18 12:00:00")
def test_create_tokens_from_oauth_payload(monkeypatch, id_token, id_payload):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(return_value=mocked_jwt_validator),
    )
    permissions_from_scope = [
        "MANAGE_ORDERS",
    ]
    auth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": (
            "openid profile email offline_access saleor:manage_orders saleor:staff"
        ),
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    user = get_or_create_user_from_payload(id_payload, "https://saleor.io/oauth")
    permissions = get_saleor_permissions_qs_from_scope(auth_payload.get("scope"))
    perms = get_saleor_permission_names(permissions)
    tokens = create_tokens_from_oauth_payload(
        auth_payload, user, id_payload, perms, "PluginID"
    )

    created_user = User.objects.get()

    token = create_jwt_token(
        id_payload,
        created_user,
        auth_payload["access_token"],
        permissions_from_scope,
        "PluginID",
    )

    assert created_user.email == id_payload["email"]
    assert tokens["token"] == token
    # confirm that we have jwt token
    decoded_token = jwt_decode(tokens["token"])
    assert decoded_token.get(PERMISSIONS_FIELD) == permissions_from_scope

    decoded_refresh_token = jwt_decode(tokens["refresh_token"])
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
def test_validate_refresh_token_missing_csrf_token(admin_user):
    token = create_jwt_refresh_token(admin_user, "refresh_token", "csrf", "pluginID")
    with pytest.raises(ValidationError):
        validate_refresh_token(token, {})


def test_validate_refresh_token_missing_csrf_token_in_token_payload(admin_user):
    additional_payload = {"oauth_refresh_token": "refresh_token"}
    jwt_payload = jwt_user_payload(
        admin_user,
        JWT_REFRESH_TYPE,
        # oauth_refresh_token has own expiration time. No need to duplicate it here
        exp_delta=None,
        additional_payload=additional_payload,
    )
    token = jwt_encode(jwt_payload)
    with pytest.raises(ValidationError):
        validate_refresh_token(token, {})


def test_validate_refresh_token_missing_token():
    refresh_token = ""
    with pytest.raises(ValidationError):
        validate_refresh_token(refresh_token, {})


def test_get_saleor_permissions_from_scope():
    auth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "scope": (
            "openid profile email offline_access saleor:manage_orders "
            "saleor:non_existing saleor saleor: saleor:manage_users"
        ),
    }
    expected_permissions = {"MANAGE_USERS", "MANAGE_ORDERS"}
    permissions = get_saleor_permissions_qs_from_scope(auth_payload.get("scope"))
    permission_names = get_saleor_permission_names(permissions)
    assert set(permission_names) == expected_permissions


def test_get_user_info_raises_decode_error(monkeypatch):
    response = Response()
    response.status_code = 200
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.requests.get", Mock(return_value=response)
    )

    user_info = get_user_info("https://saleor.io/userinfo", "access_token")
    assert user_info is None


def test_get_user_info_raises_http_error(monkeypatch):
    response = Response()
    response.status_code = 500
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.requests.get", Mock(return_value=response)
    )

    user_info = get_user_info("https://saleor.io/userinfo", "access_token")
    assert user_info is None


def test_get_or_create_user_from_payload_retrieve_user_by_sub(customer_user):
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_user.private_metadata = {f"oidc-{oauth_url}": sub_id}
    customer_user.save()

    user_from_payload = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )

    assert user_from_payload.id == customer_user.id
    assert user_from_payload.private_metadata[f"oidc-{oauth_url}"] == sub_id


def test_get_or_create_user_from_payload_updates_sub(customer_user):
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_user.private_metadata = {f"oidc-{oauth_url}": "old-sub"}
    customer_user.save()

    user_from_payload = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )

    assert user_from_payload.id == customer_user.id
    assert user_from_payload.private_metadata[f"oidc-{oauth_url}"] == sub_id


def test_get_or_create_user_from_payload_assigns_sub(customer_user):
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    user_from_payload = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )

    assert user_from_payload.id == customer_user.id
    assert user_from_payload.private_metadata[f"oidc-{oauth_url}"] == sub_id


def test_get_or_create_user_from_payload_creates_user_with_sub():
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_email = "email.customer@example.com"

    user_from_payload = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_email},
        oauth_url=oauth_url,
    )

    assert user_from_payload.email == customer_email
    assert user_from_payload.private_metadata[f"oidc-{oauth_url}"] == sub_id


def test_get_or_create_user_from_payload_multiple_subs(customer_user, admin_user):
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    customer_user.private_metadata = {f"oidc-{oauth_url}": sub_id}
    customer_user.save()

    admin_user.private_metadata = {f"oidc-{oauth_url}": sub_id}
    admin_user.save()

    with warnings.catch_warnings(record=True):
        user_from_payload = get_or_create_user_from_payload(
            payload={"sub": sub_id, "email": customer_user.email},
            oauth_url=oauth_url,
        )

    assert user_from_payload.email == customer_user.email
    assert user_from_payload.private_metadata[f"oidc-{oauth_url}"] == sub_id


def test_get_or_create_user_from_payload_different_email(customer_user):
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    new_customer_email = "new.customer@example.com"

    customer_user.private_metadata = {f"oidc-{oauth_url}": sub_id}
    customer_user.save()

    user_from_payload = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": new_customer_email},
        oauth_url=oauth_url,
    )

    customer_user.refresh_from_db()
    assert user_from_payload.id == customer_user.id
    assert customer_user.email == new_customer_email
    assert customer_user.private_metadata[f"oidc-{oauth_url}"] == sub_id


@freeze_time("2019-03-18 12:00:00")
def test_get_or_create_user_from_payload_with_last_login(customer_user, settings):
    settings.TIME_ZONE = "UTC"
    current_ts = int(time.time())

    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    customer_user.last_login = make_aware(
        datetime.fromtimestamp(current_ts - 10), timezone=pytz.timezone("UTC")
    )
    customer_user.save()

    user_from_payload = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
        last_login=current_ts,
    )

    customer_user.refresh_from_db()
    assert customer_user.last_login == make_aware(
        datetime.fromtimestamp(current_ts), timezone=pytz.timezone("UTC")
    )
    assert user_from_payload.email == customer_user.email
    assert user_from_payload.private_metadata[f"oidc-{oauth_url}"] == sub_id
