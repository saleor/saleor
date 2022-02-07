import jwt
from jwt import PyJWK

from ..jwt_manager import get_jwt_manager


def test_jwks_can_be_used_to_decode_saleor_token(client):
    # given
    jwt_manager = get_jwt_manager()
    payload = {"A": "1", "B": "2", "C": "3"}
    token = jwt_manager.encode(payload)

    # when
    response = client.get("/.well-known/jwks.json")
    key = response.json().get("keys")[0]

    # then
    jwt.decode(token, PyJWK.from_dict(key, algorithm="RS256").key, algorithms=["RS256"])
