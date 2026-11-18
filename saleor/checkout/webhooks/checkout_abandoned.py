from collections import defaultdict
from collections.abc import Iterable
from functools import partial
from typing import TYPE_CHECKING

from django.conf import settings

from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.payloads import generate_checkout_payload
from ...webhook.transport.asynchronous.transport import (
    WebhookPayloadData,
    trigger_webhooks_async_for_multiple_objects,
)

if TYPE_CHECKING:
    from ...webhook.models import Webhook
    from ..models import Checkout


def trigger_checkout_abandoned(
    checkouts: Iterable["Checkout"],
    webhooks_per_channel: dict[int, list["Webhook"]],
) -> None:
    checkouts_per_channel: dict[int, list[Checkout]] = defaultdict(list)
    for checkout in checkouts:
        checkouts_per_channel[checkout.channel_id].append(checkout)

    for channel_id, channel_checkouts in checkouts_per_channel.items():
        trigger_webhooks_async_for_multiple_objects(
            WebhookEventAsyncType.CHECKOUT_ABANDONED,
            webhooks_per_channel[channel_id],
            webhook_payloads_data=[
                WebhookPayloadData(
                    subscribable_object=checkout,
                    legacy_data_generator=partial(generate_checkout_payload, checkout),
                )
                for checkout in channel_checkouts
            ],
            queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        )
