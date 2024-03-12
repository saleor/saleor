import json

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from ..jwt_manager import JWTManager, get_jwt_manager


def test_get_jwt_manager(settings):
    # given
    assert settings.JWT_MANAGER_PATH == "saleor.core.jwt_manager.JWTManager"

    # when
    jwt_manager = get_jwt_manager()

    # then
    assert jwt_manager == JWTManager


@override_settings(RSA_PRIVATE_KEY=None)
def test_jwt_manager_validate_missing_rsa_private_key(settings):
    # given
    jwt_manager = get_jwt_manager()

    # when & then
    with pytest.raises(ImproperlyConfigured):
        jwt_manager.validate_configuration()


@override_settings(RSA_PRIVATE_KEY="WRONG-FORMAT")
def test_jwt_manager_validate_incorrect_format_of_rsa_private_key(settings):
    # given
    jwt_manager = get_jwt_manager()

    # when & then
    with pytest.raises(ImproperlyConfigured):
        jwt_manager.validate_configuration()


def test_jwt_manager_encode(settings):
    # given
    payload = {"A": "1", "B": "2"}
    jwt_manager = get_jwt_manager()
    private_key = serialization.load_pem_private_key(
        settings.RSA_PRIVATE_KEY.encode("utf-8"), password=settings.RSA_PRIVATE_PASSWORD
    )

    # when
    token = jwt_manager.encode(payload)

    # then
    headers = jwt.get_unverified_header(token)
    decoded_token = jwt.decode(
        token,
        private_key.public_key(),
        algorithms=["RS256"],
    )

    assert decoded_token == payload
    assert headers == {"alg": "RS256", "kid": jwt_manager.get_key_id(), "typ": "JWT"}


def test_jwt_manager_jws_encode(settings):
    # given
    payload = {"A": "1", "B": "2"}
    encoded_payload = json.dumps(payload).encode()
    jwt_manager = get_jwt_manager()
    private_key = serialization.load_pem_private_key(
        settings.RSA_PRIVATE_KEY.encode("utf-8"), password=settings.RSA_PRIVATE_PASSWORD
    )

    # when
    token = jwt_manager.jws_encode(encoded_payload)

    # then
    headers = jwt.get_unverified_header(token)
    decoded_token = jwt.decode(
        token,
        private_key.public_key(),
        algorithms=["RS256"],
        detached_payload=encoded_payload,
    )
    assert decoded_token == payload
    assert headers == {
        "alg": "RS256",
        "b64": False,
        "crit": ["b64"],
        "kid": jwt_manager.get_key_id(),
        "typ": "JWT",
    }


def test_jwt_manager_decode_token_signed_with_rs256(settings):
    # given
    payload = {"A": "1", "B": "2"}
    private_key = serialization.load_pem_private_key(
        settings.RSA_PRIVATE_KEY.encode("utf-8"), password=settings.RSA_PRIVATE_PASSWORD
    )
    token = jwt.encode(payload, private_key, algorithm="RS256")
    jwt_manager = get_jwt_manager()

    # when
    decoded_token = jwt_manager.decode(token)

    # then
    assert decoded_token == payload


def test_jwt_manager_decode_token_signed_with_hs256(settings):
    # given
    payload = {"A": "1", "B": "2"}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    jwt_manager = get_jwt_manager()

    # when
    decoded_token = jwt_manager.decode(token)

    # then
    assert decoded_token == payload
