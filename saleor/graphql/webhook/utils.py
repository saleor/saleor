import hashlib
import logging
from typing import Optional

from ...webhook.models import Webhook

logger = logging.getLogger(__name__)


def get_subscription_query_hash(subscription_query: str) -> str:
    return hashlib.md5(subscription_query.encode("utf-8")).hexdigest()


def get_pregenerated_subscription_payload(
    webhook: Webhook,
    pregenerated_subscription_payloads: Optional[dict] = None,
) -> Optional[dict]:
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    if webhook.subscription_query is None or pregenerated_subscription_payloads is None:
        return None

    query_hash = get_subscription_query_hash(webhook.subscription_query)
    return pregenerated_subscription_payloads.get(webhook.app_id, {}).get(
        query_hash, None
    )
