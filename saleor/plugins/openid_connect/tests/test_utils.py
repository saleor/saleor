import json
from unittest.mock import MagicMock, Mock

import pytest
import requests
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from saleor.account.models import User
from saleor.core.jwt import (
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)

from ..exceptions import AuthenticationError
from ..utils import (
    create_jwt_refresh_token,
    create_jwt_token,
    create_tokens_from_oauth_payload,
    fetch_jwks,
    get_or_create_user_from_token,
    get_saleor_permissions_from_scope,
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
def test_fetch_jwks():
    jwks_url = "https://saleor-test.eu.auth0.com/.well-known/jwks.json"
    keys = fetch_jwks(jwks_url)
    assert len(keys) == 2


@freeze_time("2019-03-18 12:00:00")
def test_create_tokens_from_oauth_payload(
    monkeypatch, id_token, id_payload, admin_user
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.jwt.decode",
        Mock(return_value=mocked_jwt_validator),
    )
    permissions_from_scope = [
        "MANAGE_ORDERS",
    ]
    auth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": ("openid profile email offline_access saleor:manage_orders"),
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    user = get_or_create_user_from_token(id_payload)
    perms = get_saleor_permissions_from_scope(auth_payload.get("scope"))
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

    decoded_refresh_token = jwt_decode(tokens["refreshToken"])
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
def test_validate_refresh_token_missing_csrf_token(id_payload, admin_user):
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
    permissions = get_saleor_permissions_from_scope(auth_payload.get("scope"))
    assert set(permissions) == expected_permissions
