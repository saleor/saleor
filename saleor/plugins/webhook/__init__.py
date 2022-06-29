import hashlib
import hmac

from ...core.jwt_manager import get_jwt_manager


def signature_for_payload(body: bytes, secret_key):
    if secret_key is None:
        return get_jwt_manager().jws_encode(body)
    hash = hmac.new(bytes(secret_key, "utf-8"), body, hashlib.sha256)
    return hash.hexdigest()
