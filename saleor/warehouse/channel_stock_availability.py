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


def trigger_out_of_stock_in_channel_events_for_stocks(
    stocks: list[Stock],
    site_settings: "SiteSettings",
    requestor: "User | App | None" = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    """Bulk version of `trigger_out_of_stock_in_channel_events`.

    Batches the channel/warehouse/availability queries across all stocks so the
    total query count stays constant (~5) regardless of batch size.
    """
    _trigger_channel_stock_events_for_stocks(
        stocks,
        site_settings,
        requestor,
        webhooks,
        cc_trigger=trigger_product_variant_out_of_stock_for_click_and_collect,
        non_cc_trigger=trigger_product_variant_out_of_stock_in_channel,
    )


def trigger_back_in_stock_in_channel_events_for_stocks(
    stocks: list[Stock],
    site_settings: "SiteSettings",
    requestor: "User | App | None" = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    """Bulk version of `trigger_back_in_stock_in_channel_events`.

    Batches the channel/warehouse/availability queries across all stocks so the
    total query count stays constant (~5) regardless of batch size.
    """
    _trigger_channel_stock_events_for_stocks(
        stocks,
        site_settings,
        requestor,
        webhooks,
        cc_trigger=trigger_product_variant_back_in_stock_for_click_and_collect,
        non_cc_trigger=trigger_product_variant_back_in_stock_in_channel,
    )


def _trigger_channel_stock_events_for_stocks(
    stocks: list[Stock],
    site_settings: "SiteSettings",
    requestor: "User | App | None",
    webhooks: "QuerySet[Webhook] | None",
    cc_trigger,
    non_cc_trigger,
) -> None:
    if not stocks:
        return

    cc_stocks: list[Stock] = []
    non_cc_stocks: list[Stock] = []
    for stock in stocks:
        if _is_click_and_collect_warehouse(stock):
            cc_stocks.append(stock)
        else:
            non_cc_stocks.append(stock)

    for bucket_stocks, trigger, cc_options in [
        (cc_stocks, cc_trigger, CC_OPTIONS),
        (non_cc_stocks, non_cc_trigger, [WarehouseClickAndCollectOption.DISABLED]),
    ]:
        if not bucket_stocks:
            continue
        for (
            stock,
            channel_slug,
        ) in _get_channels_without_other_available_warehouses_bulk(
            bucket_stocks, cc_options
        ):
            trigger(
                VariantChannelStockInfo(
                    variant_id=stock.product_variant_id,
                    channel_slug=channel_slug,
                ),
                site_settings,
                requestor=requestor,
                webhooks=webhooks,
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


def _get_channels_without_other_available_warehouses_bulk(
    stocks: list[Stock], cc_options: list[str]
) -> list[tuple[Stock, str]]:
    """Return (stock, channel_slug) pairs with no other same-kind warehouse availability.

    For each stock, checks every channel its warehouse belongs to. If no other
    warehouse of the same kind (C&C or non-C&C) in that channel has available
    quantity for the stock's variant, the (stock, channel_slug) pair is included
    in the result.
    """
    stock_ids = [stock.id for stock in stocks]
    warehouse_ids = list({stock.warehouse_id for stock in stocks})

    # Find all warehouses of the same C&C kind in channels that contain any of
    # the source stocks' warehouses. Source warehouses are included because
    # warehouse A may serve as "the other warehouse" for a stock in warehouse B.
    source_channels = ChannelWarehouse.objects.filter(
        warehouse_id__in=warehouse_ids,
        channel_id=OuterRef("channel_id"),
    )
    channel_warehouses = ChannelWarehouse.objects.filter(Exists(source_channels))
    matching_warehouses = Warehouse.objects.filter(
        Exists(channel_warehouses.filter(warehouse_id=OuterRef("pk"))),
        click_and_collect_option__in=cc_options,
    )

    # Fetch available quantity per (warehouse, variant) for all relevant
    # variants, excluding the source stocks themselves.
    variant_ids = list({stock.product_variant_id for stock in stocks})
    available_rows = (
        Stock.objects.filter(
            Exists(matching_warehouses.filter(pk=OuterRef("warehouse_id"))),
            product_variant_id__in=variant_ids,
        )
        .exclude(id__in=stock_ids)
        .annotate_available_quantity()
        .values_list("warehouse_id", "product_variant_id", "available_quantity")
    )

    available_by_warehouse_variant: dict[tuple[UUID, int], int] = defaultdict(int)
    availability_warehouse_ids: set[UUID] = set()
    for warehouse_id, variant_id, available_quantity in available_rows:
        available_by_warehouse_variant[(warehouse_id, variant_id)] += max(
            available_quantity, 0
        )
        availability_warehouse_ids.add(warehouse_id)

    # Map warehouse ids back to their channels. Includes both the warehouses
    # from the availability results and the source stocks' warehouses so the
    # final loop can resolve channel slugs for each stock.
    warehouse_id_to_channels_map = _get_warehouse_to_channels_map(
        list(availability_warehouse_ids | set(warehouse_ids))
    )

    # Group stocks by variant so we can match availability rows to stocks.
    variant_id_to_stocks: dict[int, list[Stock]] = defaultdict(list)
    for stock in stocks:
        variant_id_to_stocks[stock.product_variant_id].append(stock)

    # Accumulate available quantity per (stock, channel) from other warehouses.
    # A warehouse is skipped for a stock when it is the stock's own warehouse.
    channel_available_per_stock: dict[tuple[int, int], int] = defaultdict(int)
    for (
        warehouse_id,
        variant_id,
    ), available_quantity in available_by_warehouse_variant.items():
        warehouse_channels = warehouse_id_to_channels_map.get(warehouse_id, [])
        for stock in variant_id_to_stocks.get(variant_id, []):
            if warehouse_id == stock.warehouse_id:
                continue
            for channel_id, _ in warehouse_channels:
                channel_available_per_stock[(stock.id, channel_id)] += (
                    available_quantity
                )

    # Return (stock, channel_slug) for channels where no other warehouse has
    # availability for the stock's variant.
    result: list[tuple[Stock, str]] = []
    for stock in stocks:
        for channel_id, channel_slug in warehouse_id_to_channels_map.get(
            stock.warehouse_id, []
        ):
            if channel_available_per_stock.get((stock.id, channel_id), 0) == 0:
                result.append((stock, channel_slug))

    return result


def _get_warehouse_to_channels_map(
    warehouse_ids: list[UUID],
) -> dict[UUID, list[tuple[int, str]]]:
    warehouse_to_channels: dict[UUID, list[tuple[int, str]]] = defaultdict(list)
    for channel_id, channel_slug, warehouse_id in ChannelWarehouse.objects.filter(
        warehouse_id__in=warehouse_ids
    ).values_list("channel_id", "channel__slug", "warehouse_id"):
        warehouse_to_channels[warehouse_id].append((channel_id, channel_slug))
    return warehouse_to_channels


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
