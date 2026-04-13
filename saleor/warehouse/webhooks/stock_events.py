from collections.abc import Iterable
from functools import partial
from typing import TYPE_CHECKING

from ...account.models import User
from ...app.models import App
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.transport.asynchronous.transport import (
    WebhookPayloadData,
    trigger_webhooks_async,
    trigger_webhooks_async_for_multiple_objects,
)
from ...webhook.utils import get_webhooks_for_event
from .payloads import generate_product_variant_with_stock_payload

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...webhook.models import Webhook
    from ..models import Stock


T_REQUESTOR = User | App | None


def trigger_product_variant_out_of_stock(
    stock: "Stock",
    requestor: T_REQUESTOR,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
    if webhooks is None:
        webhooks = get_webhooks_for_event(event_type)
    if not webhooks:
        return
    legacy_data_generator = partial(
        generate_product_variant_with_stock_payload, [stock], requestor
    )
    trigger_webhooks_async(
        None,
        event_type,
        webhooks,
        subscribable_object=stock,
        requestor=requestor,
        legacy_data_generator=legacy_data_generator,
    )


def trigger_product_variant_back_in_stock(
    stock: "Stock",
    requestor: T_REQUESTOR,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
    if webhooks is None:
        webhooks = get_webhooks_for_event(event_type)
    if not webhooks:
        return
    legacy_data_generator = partial(
        generate_product_variant_with_stock_payload, [stock], requestor
    )
    trigger_webhooks_async(
        None,
        event_type,
        webhooks,
        subscribable_object=stock,
        requestor=requestor,
        legacy_data_generator=legacy_data_generator,
    )


def trigger_product_variant_stocks_updated(
    stocks: Iterable["Stock"],
    requestor: T_REQUESTOR,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED
    if webhooks is None:
        webhooks = get_webhooks_for_event(event_type)
    if not webhooks:
        return
    webhook_payloads_data = [
        WebhookPayloadData(
            subscribable_object=stock,
            legacy_data_generator=partial(
                generate_product_variant_with_stock_payload, [stock], requestor
            ),
            data=None,
        )
        for stock in stocks
    ]
    trigger_webhooks_async_for_multiple_objects(
        event_type,
        webhooks,
        webhook_payloads_data=webhook_payloads_data,
        requestor=requestor,
    )
