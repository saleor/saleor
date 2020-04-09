import hashlib
import hmac
from typing import Optional

from ...site.models import Site


def create_hmac_signature(body: str, secret_key: str, encoding: str):
    b_body = bytes(body, encoding)
    hash = hmac.new(bytes(secret_key, encoding), b_body, hashlib.sha256)
    return hash.hexdigest()


def create_webhook_headers(
    event_name: str,
    body: Optional[str] = None,
    secret_key: Optional[str] = None,
    encoding: str = "utf-8",
):
    signature_prefix = "sha1="
    domain = Site.objects.get_current().domain
    headers = {"X-Saleor-Event": event_name, "X-Saleor-Domain": domain}
    if secret_key and body:
        saleor_hmac_sha256 = signature_prefix + create_hmac_signature(
            body, secret_key, encoding
        )
        headers["X-Saleor-HMAC-SHA256"] = saleor_hmac_sha256
    return headers
