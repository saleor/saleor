import hashlib
import hmac

from jwt.algorithms import get_default_algorithms

from ...core.jwt_manager import get_jwt_manager


def signature_for_payload(body: bytes, secret_key):
    if secret_key is None:
        algorithm = get_default_algorithms()["RS256"]
        private_key = get_jwt_manager().get_private_key()
        return algorithm.sign(body, private_key).hex()
    hash = hmac.new(bytes(secret_key, "utf-8"), body, hashlib.sha256)
    return hash.hexdigest()
