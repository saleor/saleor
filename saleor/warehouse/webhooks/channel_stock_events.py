import json
from typing import TYPE_CHECKING

import graphene

from ...account.models import User
from ...app.models import App
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.transport.asynchronous.transport import trigger_webhooks_async
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
    stock_info: VariantChannelStockInfo,
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR,
    webhooks: "QuerySet[Webhook] | None",
) -> None:
    # channel stock availability are only triggered when legacy shipping zone
    # stock availability is disabled
    if site_settings.use_legacy_shipping_zone_stock_availability:
        return
    if webhooks is None:
        webhooks = get_webhooks_for_event(event_type)
    channel_webhooks = filter_webhooks_for_channel(webhooks, stock_info.channel_slug)
    if not channel_webhooks:
        return
    trigger_webhooks_async(
        None,
        event_type,
        channel_webhooks,
        subscribable_object=stock_info,
        requestor=requestor,
        legacy_data_generator=lambda: _build_legacy_payload(stock_info),
    )


def trigger_product_variant_out_of_stock_in_channel(
    stock_info: VariantChannelStockInfo,
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        stock_info,
        site_settings,
        requestor,
        webhooks,
    )


def trigger_product_variant_back_in_stock_in_channel(
    stock_info: VariantChannelStockInfo,
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_IN_CHANNEL,
        stock_info,
        site_settings,
        requestor,
        webhooks,
    )


def trigger_product_variant_out_of_stock_for_click_and_collect(
    stock_info: VariantChannelStockInfo,
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_FOR_CLICK_AND_COLLECT,
        stock_info,
        site_settings,
        requestor,
        webhooks,
    )


def trigger_product_variant_back_in_stock_for_click_and_collect(
    stock_info: VariantChannelStockInfo,
    site_settings: "SiteSettings",
    requestor: T_REQUESTOR = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_FOR_CLICK_AND_COLLECT,
        stock_info,
        site_settings,
        requestor,
        webhooks,
    )
