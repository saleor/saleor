import hashlib
import hmac
from typing import Optional

from ...site.models import Site


def signature_for_payload(body: bytes, secret_key):
    hash = hmac.new(bytes(secret_key, "utf-8"), body, hashlib.sha256)
    return hash.hexdigest()


def create_webhook_headers(
    event_name: str, body: Optional[bytes] = None, secret_key: Optional[str] = None
):
    domain = Site.objects.get_current().domain
    headers = {
        "Content-Type": "application/json",
        "X-Saleor-Event": event_name,
        "X-Saleor-Domain": domain,
    }
    if secret_key and body:
        saleor_hmac_sha256 = signature_for_payload(body, secret_key)
        headers["X-Saleor-HMAC-SHA256"] = saleor_hmac_sha256
    return headers
