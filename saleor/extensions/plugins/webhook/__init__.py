import hashlib
import hmac
from typing import Optional

from ....site.models import Site


def create_webhook_headers(
    event_name: str,
    body: Optional[str] = None,
    secret_key: Optional[str] = None,
    encoding: str = "utf-8",
):
    signature_prefix = "sha1="
    domain = Site.objects.get_current().domain
    headers = {
        "X-Saleor-Event": event_name,
        # X-Saleor-Task: {TaskID} # FIXME
        "X-Saleor-Domain": domain,
    }
    if secret_key and body:
        b_body = bytes(body, encoding)
        hash = hmac.new(bytes(secret_key, encoding), b_body, hashlib.sha256)
        saleor_hmac_sha256 = signature_prefix + hash.hexdigest()
        headers["X-Saleor-HMAC-SHA256"] = saleor_hmac_sha256
    return headers
