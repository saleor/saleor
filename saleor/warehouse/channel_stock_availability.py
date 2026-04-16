from collections import defaultdict
from typing import TYPE_CHECKING
from uuid import UUID

from django.db.models import Exists, OuterRef

from . import WarehouseClickAndCollectOption
from .interface import VariantChannelStockInfo
from .models import ChannelWarehouse, Stock, Warehouse
from .webhooks.channel_stock_events import (
    trigger_product_variant_back_in_stock_for_click_and_collect,
    trigger_product_variant_back_in_stock_in_channel,
    trigger_product_variant_out_of_stock_for_click_and_collect,
    trigger_product_variant_out_of_stock_in_channel,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ..account.models import User
    from ..app.models import App
    from ..site.models import SiteSettings
    from ..webhook.models import Webhook


CC_OPTIONS = [
    WarehouseClickAndCollectOption.LOCAL_STOCK,
    WarehouseClickAndCollectOption.ALL_WAREHOUSES,
]


def trigger_out_of_stock_in_channel_events(
    stock: Stock,
    site_settings: "SiteSettings",
    requestor: "User | App | None" = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    """Fire channel-scoped OUT_OF_STOCK events for `stock`'s variant.

    For each channel where `stock`'s warehouse belongs, fires
    OUT_OF_STOCK_IN_CHANNEL (for regular warehouses) or
    OUT_OF_STOCK_FOR_CLICK_AND_COLLECT (for C&C warehouses) when no other
    warehouse of the same kind in that channel has remaining availability.

    Call after `stock` has just reached 0 available.
    """
    is_cc = _is_click_and_collect_warehouse(stock)
    # trigger for channel where there is no availability in other warehouses of
    # the same kind (C&C or non-C&C)
    for channel_slug in _get_channels_without_other_available_warehouses(stock, is_cc):
        stock_info = VariantChannelStockInfo(
            variant_id=stock.product_variant_id,
            channel_slug=channel_slug,
        )
        if is_cc:
            trigger_product_variant_out_of_stock_for_click_and_collect(
                stock_info, site_settings, requestor=requestor, webhooks=webhooks
            )
        else:
            trigger_product_variant_out_of_stock_in_channel(
                stock_info, site_settings, requestor=requestor, webhooks=webhooks
            )


def trigger_back_in_stock_in_channel_events(
    stock: Stock,
    site_settings: "SiteSettings",
    requestor: "User | App | None" = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    """Fire channel-scoped BACK_IN_STOCK events for `stock`'s variant.

    For each channel where `stock`'s warehouse belongs, fires
    BACK_IN_STOCK_IN_CHANNEL (for regular warehouses) or
    BACK_IN_STOCK_FOR_CLICK_AND_COLLECT (for C&C warehouses) when no other
    warehouse of the same kind in that channel has availability — i.e. `stock`
    is the first one back.

    Call after `stock` has just risen above 0 available.
    """
    is_cc = _is_click_and_collect_warehouse(stock)
    # when no other warehouse of the same kind (C&C or non-C&C) in that channel
    # has stock availability is the first one back, and event should be triggered
    for channel_slug in _get_channels_without_other_available_warehouses(stock, is_cc):
        stock_info = VariantChannelStockInfo(
            variant_id=stock.product_variant_id,
            channel_slug=channel_slug,
        )
        if is_cc:
            trigger_product_variant_back_in_stock_for_click_and_collect(
                stock_info, site_settings, requestor=requestor, webhooks=webhooks
            )
        else:
            trigger_product_variant_back_in_stock_in_channel(
                stock_info, site_settings, requestor=requestor, webhooks=webhooks
            )


def _is_click_and_collect_warehouse(stock: Stock) -> bool:
    return stock.warehouse.click_and_collect_option in CC_OPTIONS


def _get_channels_without_other_available_warehouses(
    stock: Stock, is_cc: bool
) -> list[str]:
    """Return slugs of channels with no other warehouse having availability.

    Returns warehouses of the same kind as `stock.warehouse` (C&C when
    `is_cc` is True, otherwise regular). A channel is included when every such
    warehouse in it — other than `stock.warehouse` — has zero available quantity
    for `stock`'s variant.
    """
    channel_pairs: list[tuple[int, str]] = list(
        ChannelWarehouse.objects.filter(warehouse_id=stock.warehouse_id).values_list(
            "channel_id", "channel__slug"
        )
    )
    if not channel_pairs:
        return []
    channel_ids = [channel[0] for channel in channel_pairs]

    cc_options = CC_OPTIONS if is_cc else [WarehouseClickAndCollectOption.DISABLED]
    channel_warehouses = ChannelWarehouse.objects.filter(
        channel_id__in=channel_ids,
    )
    warehouses = Warehouse.objects.filter(
        Exists(channel_warehouses.filter(warehouse_id=OuterRef("pk"))),
        click_and_collect_option__in=cc_options,
    ).exclude(pk=stock.warehouse_id)
    available_by_warehouse: dict[UUID, int] = dict(
        Stock.objects.filter(
            Exists(warehouses.filter(pk=OuterRef("warehouse_id"))),
            product_variant_id=stock.product_variant_id,
        )
        .annotate_available_quantity()
        .values_list("warehouse_id", "available_quantity")
    )

    warehouse_id_to_channel_map = _get_warehouse_id_to_channels_map(
        channel_ids, list(available_by_warehouse.keys())
    )
    available_qty_per_channel: dict[int, int] = defaultdict(int)
    for warehouse_id, available_quantity in available_by_warehouse.items():
        for channel_id in warehouse_id_to_channel_map.get(warehouse_id, []):
            available_qty_per_channel[channel_id] += max(available_quantity, 0)

    return [
        slug
        for channel_id, slug in channel_pairs
        if available_qty_per_channel.get(channel_id, 0) == 0
    ]


def _get_warehouse_id_to_channels_map(
    channel_ids: list[int], warehouse_ids: list[UUID]
) -> dict[UUID, list[int]]:
    warehouse_to_channels: dict[UUID, list[int]] = defaultdict(list)
    for channel_id, warehouse_id in ChannelWarehouse.objects.filter(
        warehouse_id__in=warehouse_ids,
        channel_id__in=channel_ids,
    ).values_list("channel_id", "warehouse_id"):
        warehouse_to_channels[warehouse_id].append(channel_id)
    return warehouse_to_channels
