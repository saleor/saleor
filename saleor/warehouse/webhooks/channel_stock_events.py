import json
from collections import defaultdict
from functools import partial
from typing import TYPE_CHECKING

import graphene

from ...account.models import User
from ...app.models import App
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.transport.asynchronous.transport import (
    WebhookPayloadData,
    trigger_webhooks_async_for_multiple_objects,
)
from ...webhook.utils import filter_webhooks_for_channel, get_webhooks_for_event
from ..interface import VariantChannelStockInfo

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...site.models import SiteSettings
    from ...webhook.models import Webhook


T_REQUESTOR = User | App | None


def _build_legacy_payload(stock_info: VariantChannelStockInfo) -> str:
    return json.dumps(
        {
            "product_variant_id": graphene.Node.to_global_id(
                "ProductVariant", stock_info.variant_id
            ),
            "channel": {"slug": stock_info.channel_slug},
        }
    )


def _trigger(
    event_type: str,
    stock_infos: list[VariantChannelStockInfo],
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR,
    webhooks: "QuerySet[Webhook] | None",
) -> None:
    # channel stock availability events are only triggered when legacy shipping
    # zone stock availability is disabled
    if site_settings.use_legacy_shipping_zone_stock_availability:
        return
    if not stock_infos:
        return
    if webhooks is None:
        webhooks = get_webhooks_for_event(event_type)

    stock_infos_by_channel: dict[str, list[VariantChannelStockInfo]] = defaultdict(list)
    for stock_info in stock_infos:
        stock_infos_by_channel[stock_info.channel_slug].append(stock_info)

    for channel_slug, channel_stock_infos in stock_infos_by_channel.items():
        channel_webhooks = filter_webhooks_for_channel(webhooks, channel_slug)
        if not channel_webhooks:
            continue
        trigger_webhooks_async_for_multiple_objects(
            event_type=event_type,
            webhooks=channel_webhooks,
            webhook_payloads_data=[
                WebhookPayloadData(
                    subscribable_object=stock_info,
                    legacy_data_generator=partial(_build_legacy_payload, stock_info),
                )
                for stock_info in channel_stock_infos
            ],
            requestor=requestor,
        )


def trigger_product_variant_out_of_stock_in_channel(
    stock_infos: list[VariantChannelStockInfo],
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        stock_infos,
        site_settings,
        requestor,
        webhooks,
    )


def trigger_product_variant_back_in_stock_in_channel(
    stock_infos: list[VariantChannelStockInfo],
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_IN_CHANNEL,
        stock_infos,
        site_settings,
        requestor,
        webhooks,
    )


def trigger_product_variant_out_of_stock_for_click_and_collect(
    stock_infos: list[VariantChannelStockInfo],
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_FOR_CLICK_AND_COLLECT,
        stock_infos,
        site_settings,
        requestor,
        webhooks,
    )


def trigger_product_variant_back_in_stock_for_click_and_collect(
    stock_infos: list[VariantChannelStockInfo],
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_FOR_CLICK_AND_COLLECT,
        stock_infos,
        site_settings,
        requestor,
        webhooks,
    )
