import json
from dataclasses import dataclass

from django.urls import reverse

from ..core.utils import build_absolute_uri
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.transport.asynchronous.transport import trigger_webhooks_async
from ..webhook.utils import get_webhooks_for_event


@dataclass(frozen=True)
class SaleorApiUrlChange:
    previous_saleor_api_url: str
    saleor_api_url: str


def notify_saleor_api_url_changed(
    previous_domain: str, new_domain: str
) -> SaleorApiUrlChange:
    """Tell apps that the Saleor API URL changed from one domain to another.

    Apps store their auth data keyed by `Saleor-Api-Url`, so every delivery of this
    event, retries included, carries the previous URL in that header, letting apps
    find and re-key their data. Delivery is asynchronous and best effort.

    Call it after the transaction that changes the domain commits (e.g. from
    `transaction.on_commit`). Raises `ValueError` when the API URL does not change,
    which is also the case when `PUBLIC_URL` is set, as it overrides the domain.
    """
    change = SaleorApiUrlChange(
        previous_saleor_api_url=build_absolute_uri(reverse("api"), previous_domain),
        saleor_api_url=build_absolute_uri(reverse("api"), new_domain),
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
