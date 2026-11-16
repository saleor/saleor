import json
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from django.urls import reverse

from ..core.utils import build_absolute_uri
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.transport.asynchronous.transport import trigger_webhooks_async
from ..webhook.utils import get_webhooks_for_event


@dataclass(frozen=True)
class SaleorApiUrlChange:
    previous_saleor_api_url: str
    saleor_api_url: str


def notify_saleor_api_url_changed(new_public_url: str) -> SaleorApiUrlChange:
    """Tell apps that the Saleor API URL is about to change.

    Run it before the change: the previous URL is the current one. Apps store their
    auth data keyed by `Saleor-Api-Url`, so every delivery of this event, retries
    included, carries the previous URL in that header, letting apps find and re-key
    their data. Delivery is asynchronous and best effort.
    """
    parsed = urlparse(new_public_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"Invalid public URL: {new_public_url!r}. Expected http(s)://<host>."
        )
    change = SaleorApiUrlChange(
        previous_saleor_api_url=build_absolute_uri(reverse("api")),
        saleor_api_url=urljoin(new_public_url, reverse("api")),
    )
    if change.previous_saleor_api_url == change.saleor_api_url:
        raise ValueError(
            f"Saleor API URL is already {change.saleor_api_url!r}; nothing changes."
        )

    event_type = WebhookEventAsyncType.SALEOR_API_URL_CHANGED
    if webhooks := get_webhooks_for_event(event_type):
        trigger_webhooks_async(
            json.dumps(
                {
                    "previousSaleorApiUrl": change.previous_saleor_api_url,
                    "saleorApiUrl": change.saleor_api_url,
                }
            ),
            event_type,
            webhooks,
            subscribable_object=change,
            saleor_api_url=change.previous_saleor_api_url,
        )
    return change
