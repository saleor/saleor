import json
from unittest.mock import MagicMock, Mock

import jwt
import pytest
import requests
from django.core.exceptions import ValidationError
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


@pytest.fixture()
def id_payload():
    return {
        "given_name": "Saleor",
        "family_name": "Admin",
        "nickname": "saloer",
        "name": "Saleor Admin",
        "picture": "",
        "locale": "pl",
        "updated_at": "2020-09-22T08:50:50.110Z",
        "email": "admin@example.com",
        "email_verified": True,
        "iss": "https://saleor-test.eu.auth0.com/",
        "sub": "google-oauth2|",
        "aud": "",
        "iat": 1600764712,
        "exp": 1600800712,
    }


@pytest.fixture()
def id_token(id_payload):
    private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAnzyis1ZjfNB0bBgKFMSvvkTtwlvBsaJq7S5wA+kzeVOVpVWw
kWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHcaT92whREFpLv9cj5lTeJSibyr/Mr
m/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIytvHWTxZYEcXLgAXFuUuaS3uF9gEi
NQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0e+lf4s4OxQawWD79J9/5d3Ry0vbV
3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWbV6L11BWkpzGXSW4Hv43qa+GSYOD2
QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9MwIDAQABAoIBACiARq2wkltjtcjs
kFvZ7w1JAORHbEufEO1Eu27zOIlqbgyAcAl7q+/1bip4Z/x1IVES84/yTaM8p0go
amMhvgry/mS8vNi1BN2SAZEnb/7xSxbflb70bX9RHLJqKnp5GZe2jexw+wyXlwaM
+bclUCrh9e1ltH7IvUrRrQnFJfh+is1fRon9Co9Li0GwoN0x0byrrngU8Ak3Y6D9
D8GjQA4Elm94ST3izJv8iCOLSDBmzsPsXfcCUZfmTfZ5DbUDMbMxRnSo3nQeoKGC
0Lj9FkWcfmLcpGlSXTO+Ww1L7EGq+PT3NtRae1FZPwjddQ1/4V905kyQFLamAA5Y
lSpE2wkCgYEAy1OPLQcZt4NQnQzPz2SBJqQN2P5u3vXl+zNVKP8w4eBv0vWuJJF+
hkGNnSxXQrTkvDOIUddSKOzHHgSg4nY6K02ecyT0PPm/UZvtRpWrnBjcEVtHEJNp
bU9pLD5iZ0J9sbzPU/LxPmuAP2Bs8JmTn6aFRspFrP7W0s1Nmk2jsm0CgYEAyH0X
+jpoqxj4efZfkUrg5GbSEhf+dZglf0tTOA5bVg8IYwtmNk/pniLG/zI7c+GlTc9B
BwfMr59EzBq/eFMI7+LgXaVUsM/sS4Ry+yeK6SJx/otIMWtDfqxsLD8CPMCRvecC
2Pip4uSgrl0MOebl9XKp57GoaUWRWRHqwV4Y6h8CgYAZhI4mh4qZtnhKjY4TKDjx
QYufXSdLAi9v3FxmvchDwOgn4L+PRVdMwDNms2bsL0m5uPn104EzM6w1vzz1zwKz
5pTpPI0OjgWN13Tq8+PKvm/4Ga2MjgOgPWQkslulO/oMcXbPwWC3hcRdr9tcQtn9
Imf9n2spL/6EDFId+Hp/7QKBgAqlWdiXsWckdE1Fn91/NGHsc8syKvjjk1onDcw0
NvVi5vcba9oGdElJX3e9mxqUKMrw7msJJv1MX8LWyMQC5L6YNYHDfbPF1q5L4i8j
8mRex97UVokJQRRA452V2vCO6S5ETgpnad36de3MUxHgCOX3qL382Qx9/THVmbma
3YfRAoGAUxL/Eu5yvMK8SAt/dJK6FedngcM3JEFNplmtLYVLWhkIlNRGDwkg3I5K
y18Ae9n7dHVueyslrb6weq7dTkYDi3iOYRW8HRkIQh06wEdbxt0shTzAJvvCQfrB
jg/3747WSsf/zBTcHihTRBdAv6OmdhV4/dD5YBfLAkLrd+mX7iE=
-----END RSA PRIVATE KEY-----"""
    return jwt.encode(
        id_payload, private_key, "RS256",  # type: ignore
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
    monkeypatch, id_token, id_payload
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

    expected_tokens = {
        "token": create_jwt_token(
            id_payload, created_user, auth_payload["access_token"]
        ),
        "refreshToken": "refresh",
    }

    assert created_user.email == id_payload["email"]
    assert tokens == expected_tokens
    # confirm that we have jwt token
    jwt_decode(tokens["token"])


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

    with pytest.raises(ValidationError):
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
