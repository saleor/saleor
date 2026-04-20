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


def trigger_out_of_stock_in_channel_events_for_stocks(
    stocks: list[Stock],
    site_settings: "SiteSettings",
    requestor: "User | App | None" = None,
    webhooks: "QuerySet[Webhook] | None" = None,
    source_warehouse_to_channels: dict[UUID, list[tuple[int, str]]] | None = None,
    source_warehouse_cc_option: str | None = None,
) -> None:
    """Fire channel-scoped OUT_OF_STOCK events for each `stock`'s variant.

    For each channel where `stock`'s warehouse belongs, fires
    OUT_OF_STOCK_IN_CHANNEL (for regular warehouses) or
    OUT_OF_STOCK_FOR_CLICK_AND_COLLECT (for C&C warehouses) when no other
    warehouse of the same kind in that channel has remaining availability.

    `source_warehouse_to_channels` is an optional pre-fetched channel mapping
    for the source warehouses, and `source_warehouse_cc_option` is the shared
    click-and-collect option for all source stocks (they all come from the
    same warehouse in this path). Pass both when the source warehouse (and
    its `ChannelWarehouse` row) will no longer be reachable at event-fire
    time — e.g. during `WarehouseDelete`, capture the snapshot before the
    warehouse is deleted and forward via `call_event`.
    """
    if not stocks:
        return

    cc_stocks, non_cc_stocks = _split_stocks_by_click_and_collect(
        stocks, source_warehouse_cc_option
    )

    NON_CC_OPTIONS = [WarehouseClickAndCollectOption.DISABLED]
    stocks_trigger_cc_options = [
        (
            cc_stocks,
            trigger_product_variant_out_of_stock_for_click_and_collect,
            CC_OPTIONS,
        ),
        (
            non_cc_stocks,
            trigger_product_variant_out_of_stock_in_channel,
            NON_CC_OPTIONS,
        ),
    ]
    for grouped_stocks, trigger, cc_options in stocks_trigger_cc_options:
        if not grouped_stocks:
            continue

        stock_infos = [
            VariantChannelStockInfo(variant_id=variant_id, channel_slug=channel_slug)
            for variant_id, channel_slug in (
                _get_variant_channels_without_other_availability(
                    grouped_stocks, cc_options, source_warehouse_to_channels=source_warehouse_to_channels,
                )
            )
        ]
        if not stock_infos:
            continue
        trigger(
            stock_infos,
            site_settings,
            requestor=requestor,
            webhooks=webhooks,
        )


def trigger_back_in_stock_in_channel_events_for_stocks(
    stocks: list[Stock],
    site_settings: "SiteSettings",
    requestor: "User | App | None" = None,
    webhooks: "QuerySet[Webhook] | None" = None,
) -> None:
    """Fire channel-scoped BACK_IN_STOCK events for each `stock`'s variant.

    For each channel where `stock`'s warehouse belongs, fires
    BACK_IN_STOCK_IN_CHANNEL (for regular warehouses) or
    BACK_IN_STOCK_FOR_CLICK_AND_COLLECT (for C&C warehouses) when no other
    warehouse of the same kind in that channel has availability — i.e. `stock`
    is the first one back.
    """
    if not stocks:
        return

    cc_stocks, non_cc_stocks = _split_stocks_by_click_and_collect(stocks)

    NON_CC_OPTIONS = [WarehouseClickAndCollectOption.DISABLED]
    stocks_trigger_cc_options = [
        (
            cc_stocks,
            trigger_product_variant_back_in_stock_for_click_and_collect,
            CC_OPTIONS,
        ),
        (
            non_cc_stocks,
            trigger_product_variant_back_in_stock_in_channel,
            NON_CC_OPTIONS,
        ),
    ]
    for grouped_stocks, trigger, cc_options in stocks_trigger_cc_options:
        if not grouped_stocks:
            continue

        stock_infos = [
            VariantChannelStockInfo(variant_id=variant_id, channel_slug=channel_slug)
            for variant_id, channel_slug in (
                _get_variant_channels_without_other_availability(
                    grouped_stocks, cc_options
                )
            )
        ]
        if not stock_infos:
            continue
        trigger(
            stock_infos,
            site_settings,
            requestor=requestor,
            webhooks=webhooks,
        )


def _split_stocks_by_click_and_collect(
    stocks: list[Stock],
    source_warehouse_cc_option: str | None = None,
) -> tuple[list[Stock], list[Stock]]:
    """Partition stocks into (cc_stocks, non_cc_stocks) with a single DB query.

    Queries which warehouses among the stocks' warehouses are non-C&C
    (`click_and_collect_option=DISABLED`); everything else is treated as C&C.

    When `source_warehouse_cc_option` is provided all stocks share a single
    source warehouse with that C&C option and the split is resolved without
    querying — needed when the source warehouse is already deleted.
    """
    if source_warehouse_cc_option is not None:
        if source_warehouse_cc_option == WarehouseClickAndCollectOption.DISABLED:
            return [], list(stocks)
        return list(stocks), []

    warehouse_ids = {stock.warehouse_id for stock in stocks}
    non_cc_warehouse_ids = set(
        Warehouse.objects.filter(
            id__in=warehouse_ids,
            click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
        ).values_list("id", flat=True)
    )
    cc_stocks: list[Stock] = []
    non_cc_stocks: list[Stock] = []
    for stock in stocks:
        if stock.warehouse_id in non_cc_warehouse_ids:
            non_cc_stocks.append(stock)
        else:
            cc_stocks.append(stock)
    return cc_stocks, non_cc_stocks


def _get_variant_channels_without_other_availability(
    stocks: list[Stock],
    cc_options: list[str],
    source_warehouse_to_channels: dict[UUID, list[tuple[int, str]]] | None = None,
) -> set[tuple[int, str]]:
    """Return (variant_id, channel_slug) pairs where the source stocks are the only availability.

    For each stock, inspects every channel its warehouse belongs to. A pair is
    included when no other warehouse of the same kind (C&C or non-C&C) in that
    channel has available quantity for the stock's variant. Deduplicated so that
    multiple stocks for the same variant produce only one entry per channel.

    When `source_warehouse_to_channels` is provided, it is used for the source
    warehouses instead of querying `ChannelWarehouse` — needed when source
    warehouses are already deleted by the time this runs.
    """
    source_warehouse_ids = {stock.warehouse_id for stock in stocks}

    available_by_warehouse_and_variant = (
        _fetch_other_warehouses_availability_per_variant(
            stocks, cc_options, source_warehouse_to_channels
        )
    )

    availability_warehouse_ids = {
        warehouse_id for warehouse_id, _ in available_by_warehouse_and_variant
    }
    if source_warehouse_to_channels is not None:
        other_ids = availability_warehouse_ids - set(source_warehouse_to_channels)
        warehouse_id_to_channels_map = {
            **source_warehouse_to_channels,
            **get_warehouse_to_channels_map(list(other_ids)),
        }
    else:
        warehouse_id_to_channels_map = get_warehouse_to_channels_map(
            list(availability_warehouse_ids | source_warehouse_ids)
        )

    channel_available_per_stock = _sum_channel_availability_per_stock(
        stocks, available_by_warehouse_and_variant, warehouse_id_to_channels_map
    )

    result: set[tuple[int, str]] = set()
    for stock in stocks:
        for channel_id, channel_slug in warehouse_id_to_channels_map.get(
            stock.warehouse_id, []
        ):
            if channel_available_per_stock.get((stock.id, channel_id), 0) == 0:
                result.add((stock.product_variant_id, channel_slug))

    return result


def _fetch_other_warehouses_availability_per_variant(
    stocks: list[Stock],
    cc_options: list[str],
    source_warehouse_to_channels: dict[UUID, list[tuple[int, str]]] | None = None,
) -> dict[tuple[UUID, int], int]:
    """Fetch available quantity per (warehouse_id, variant_id) excluding source stocks.

    Considers only warehouses of the matching C&C kind in channels that contain
    any source stock's warehouse. Source warehouses themselves are included in
    the scope because warehouse A may serve as "the other warehouse" for a stock
    in warehouse B. The source stock rows are excluded from the aggregation so
    the returned map represents availability from everywhere *except* the
    source stocks.

    When `source_warehouse_to_channels` is provided, the source channel IDs are
    derived from the snapshot instead of from `ChannelWarehouse` — needed when
    source warehouses are already deleted.
    """
    stock_ids = [stock.id for stock in stocks]
    warehouse_ids = list({stock.warehouse_id for stock in stocks})
    variant_ids = list({stock.product_variant_id for stock in stocks})

    if source_warehouse_to_channels is not None:
        source_channel_ids = {
            channel_id
            for channels in source_warehouse_to_channels.values()
            for channel_id, _ in channels
        }
        channel_warehouses = ChannelWarehouse.objects.filter(
            channel_id__in=source_channel_ids
        )
    else:
        source_channels = ChannelWarehouse.objects.filter(
            warehouse_id__in=warehouse_ids,
            channel_id=OuterRef("channel_id"),
        )
        channel_warehouses = ChannelWarehouse.objects.filter(Exists(source_channels))
    matching_warehouses = Warehouse.objects.filter(
        Exists(channel_warehouses.filter(warehouse_id=OuterRef("pk"))),
        click_and_collect_option__in=cc_options,
    )

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
    for warehouse_id, variant_id, available_quantity in available_rows:
        available_by_warehouse_variant[(warehouse_id, variant_id)] += max(
            available_quantity, 0
        )
    return available_by_warehouse_variant


def _sum_channel_availability_per_stock(
    stocks: list[Stock],
    available_by_warehouse_variant: dict[tuple[UUID, int], int],
    warehouse_id_to_channels_map: dict[UUID, list[tuple[int, str]]],
) -> dict[tuple[int, int], int]:
    """Sum available quantity per (stock_id, channel_id) from warehouses other than the stock's own.

    For each availability row, distributes its quantity across the channels its
    warehouse belongs to, attributing it to every stock of the same variant
    except the stock located in the same warehouse.
    """
    variant_id_to_stocks: dict[int, list[Stock]] = defaultdict(list)
    for stock in stocks:
        variant_id_to_stocks[stock.product_variant_id].append(stock)

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
    return channel_available_per_stock


def get_warehouse_to_channels_map(
    warehouse_ids: list[UUID],
) -> dict[UUID, list[tuple[int, str]]]:
    """Return `{warehouse_id: [(channel_id, channel_slug), ...]}` for given warehouses.

    Call before a warehouse delete to capture the mapping, then pass the result
    as `source_warehouse_to_channels` to
    `trigger_out_of_stock_in_channel_events_for_stocks` via `call_event`.
    """
    warehouse_to_channels: dict[UUID, list[tuple[int, str]]] = defaultdict(list)
    for channel_id, channel_slug, warehouse_id in ChannelWarehouse.objects.filter(
        warehouse_id__in=warehouse_ids
    ).values_list("channel_id", "channel__slug", "warehouse_id"):
        warehouse_to_channels[warehouse_id].append((channel_id, channel_slug))
    return warehouse_to_channels
