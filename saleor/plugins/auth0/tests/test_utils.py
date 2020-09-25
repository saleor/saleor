import json
from unittest.mock import MagicMock, Mock

import pytest
import requests
from freezegun import freeze_time

from saleor.account.models import User
from saleor.core.jwt import jwt_decode

from ..exceptions import AuthenticationError
from ..utils import (
    create_jwt_token,
    fetch_jwks,
    get_valid_auth_tokens_from_auth0_payload,
    prepare_redirect_url,
)


def test_prepare_redirect_url():
    plugin_id = "test.auth.auth0"
    storefront_url = "http://localhost:3000/"
    url = prepare_redirect_url(plugin_id, storefront_url)
    expected_redirect = (
        "http://mirumee.com/plugins/test.auth.auth0/callback?"
        "redirectUrl=http%3A%2F%2Flocalhost%3A3000%2F"
    )
    assert url == expected_redirect


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
    monkeypatch.setattr("saleor.plugins.auth0.utils.requests.get", mocked_get)

    with pytest.raises(AuthenticationError):
        fetch_jwks(jwks_url)


@pytest.mark.vcr
def test_fetch_jwks():
    jwks_url = "https://saleor-test.eu.auth0.com/.well-known/jwks.json"
    keys = fetch_jwks(jwks_url)
    assert len(keys) == 2


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_get_valid_auth_tokens_from_auth0_payload_creates_user(
    monkeypatch, id_token, id_payload, admin_user
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.auth0.utils.jwt.decode", Mock(return_value=mocked_jwt_validator)
    )
    auth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    tokens = get_valid_auth_tokens_from_auth0_payload(
        auth_payload, "saleor-test.eu.auth0.com", get_or_create=True
    )

    created_user = User.objects.get()

    token = create_jwt_token(id_payload, created_user, auth_payload["access_token"])

    assert created_user.email == id_payload["email"]
    assert tokens["token"] == token
    # confirm that we have jwt token
    jwt_decode(tokens["token"])

    decoded_refresh_token = jwt_decode(tokens["refreshToken"])
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_get_valid_auth_tokens_from_auth0_payload_missing_user(
    monkeypatch, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.auth0.utils.jwt.decode", Mock(return_value=mocked_jwt_validator)
    )
    # user_from_token = User.objects.create(email="admin@example.com", is_active=True)
    auth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }

    with pytest.raises(AuthenticationError):
        get_valid_auth_tokens_from_auth0_payload(
            auth_payload, "saleor-test.eu.auth0.com", get_or_create=False
        )


# def get_auth_tokens_from_auth0_payload(self, token_data: dict, get_or_create=True):
#     id_token = token_data["id_token"]
#     keys = get_jwks_keys_from_cache_or_fetch(self._get_auth0_service_url(JWKS_PATH))
#
#     claims = jwt.decode(id_token, keys, claims_cls=CodeIDToken)
#     claims.validate()
#     if get_or_create:
#         user, created = User.objects.get_or_create(
#             email=claims["email"],
#             defaults={"is_active": True, "email": claims["email"]},
#         )
#     else:
#         user = User.objects.get(email=claims["email"], is_active=True)
#
#     tokens = {
#         "token": self._create_jwt_token(claims, user, token_data["access_token"]),
#     }
#     refresh_token = token_data.get("refresh_token")
#     if refresh_token:
#         tokens["refreshToken"] = refresh_token
#     return tokens
