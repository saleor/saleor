import hashlib
import hmac


def signature_for_payload(body: bytes, secret_key):
    hash = hmac.new(bytes(secret_key, "utf-8"), body, hashlib.sha256)
    return hash.hexdigest()
