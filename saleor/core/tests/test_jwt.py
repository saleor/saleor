import jwt
from cryptography.hazmat.primitives import serialization

from ..jwt import jwt_decode, jwt_encode


def test_jwt_decode_accepts_token_signed_with_hs256(settings):
    # given
    payload = {"1": "A", "2": "B"}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    # when
    decoded_token = jwt_decode(token)

    # then
    assert payload == decoded_token


def test_jwt_decode_accepts_token_signed_with_rs256(settings):
    # given
    private_key = serialization.load_pem_private_key(
        settings.RSA_PRIVATE_KEY.encode("utf-8"), password=settings.RSA_PRIVATE_PASSWORD
    )
    payload = {"1": "A", "2": "B"}
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # when
    decoded_token = jwt_decode(token)

    # then
    assert payload == decoded_token


def test_jwt_encode_creates_token_signed_with_rs256(settings):
    # given
    payload = {"1": "A", "2": "B"}

    # when
    token = jwt_encode(payload)

    # then
    headers = jwt.get_unverified_header(token)
    assert headers.get("alg") == "RS256"
