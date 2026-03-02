import functools
import math
from collections import defaultdict
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, NamedTuple, cast
from uuid import UUID

from django.db import transaction
from django.db.models import Case, F, IntegerField, Sum, Value, When
from django.db.models.expressions import Exists, OuterRef
from django.db.models.functions import Coalesce

from ..channel import AllocationStrategy
from ..checkout.models import CheckoutLine
from ..core.exceptions import (
    AllocationError,
    AllocationQuantityError,
    InsufficientStock,
    InsufficientStockData,
    PreorderAllocationError,
)
from ..core.tracing import traced_atomic_transaction
from ..core.utils.country import get_active_country
from ..order.fetch import OrderLineInfo
from ..order.models import OrderLine
from ..plugins.manager import PluginsManager
from ..product.models import ProductVariant, ProductVariantChannelListing
from .lock_objects import (
    allocation_with_stock_qs_select_for_update,
    stock_qs_select_for_update,
    stock_select_for_update_for_existing_qs,
)
from .models import (
    Allocation,
    AllocationSource,
    ChannelWarehouse,
    PreorderAllocation,
    PreorderReservation,
    Reservation,
    Stock,
    Warehouse,
)

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..inventory.models import PurchaseOrderItem
    from ..order.models import Order


class StockData(NamedTuple):
    pk: int
    quantity: int


def delete_stocks(stock_pks_to_delete: list[int]):
    with transaction.atomic():
        return Stock.objects.filter(
            id__in=Stock.objects.order_by("pk")
            .select_for_update(of=["self"])
            .values_list("pk", flat=True)
            .filter(id__in=stock_pks_to_delete)
        ).delete()


def stock_bulk_update(stocks: list[Stock], fields_to_update: list[str]):
    with transaction.atomic():
        _locked_stocks = list(
            stock_qs_select_for_update()
            .filter(id__in=[stock.id for stock in stocks])
            .values_list("id", flat=True)
        )
        Stock.objects.bulk_update(stocks, fields_to_update)


def delete_allocations(allocation_pks_to_delete: list[int]):
    with transaction.atomic():
        allocations = list(
            Allocation.objects.filter(
                id__in=Allocation.objects.order_by("stock_id")
                .select_for_update(of=["self"])
                .values_list("pk", flat=True)
                .filter(id__in=allocation_pks_to_delete)
            ).select_related("stock__warehouse")
        )

        # Deallocate sources for owned warehouses
        for allocation in allocations:
            if allocation.stock.warehouse.is_owned:
                deallocate_sources(allocation, allocation.quantity_allocated)

        # Delete allocations
        return Allocation.objects.filter(id__in=[a.id for a in allocations]).delete()


def can_confirm_order(order: "Order") -> bool:
    """Check if order can transition from UNCONFIRMED to UNFULFILLED.

    Validates that all allocations meet the requirements:
    1. Must be in owned warehouses
    2. Must have AllocationSources assigned
    3. AllocationSources must sum to quantity_allocated

    Returns False if order isn't ready (normal state), not an error.

    Returns:
        bool: True if order can be confirmed, False otherwise

    """
    from django.db.models import Q, Sum

    # Check for any violations in a single query
    violations = (
        Allocation.objects.filter(order_line__order=order)
        .annotate(total_sourced=Sum("allocation_sources__quantity"))
        .filter(
            Q(stock__warehouse__is_owned=False)  # Non-owned warehouse
            | Q(total_sourced__isnull=True)  # No sources
            | ~Q(total_sourced=F("quantity_allocated"))  # Mismatch
        )
        .exists()
    )

    has_allocations = Allocation.objects.filter(order_line__order=order).exists()

    return has_allocations and not violations


def _allocate_sources_incremental(
    allocation: Allocation,
    quantity: int,
    poi: "PurchaseOrderItem | None" = None,
):
    """Allocate sources for an incremental quantity added to existing allocation.

    Args:
        allocation: The existing Allocation to add sources to.
        quantity: The incremental quantity to allocate.
        poi: If provided, pin the source to this specific POI rather than searching
             via FIFO. Use this during PO confirmation where the batch is known.
             When None (floor stock), falls back to FIFO across available POIs.

    Raises:
        InsufficientStock: If there are not enough POI batches.

    """
    from ..inventory import PurchaseOrderItemStatus
    from ..inventory.models import PurchaseOrderItem

    if poi is not None:
        pois = PurchaseOrderItem.objects.select_for_update().filter(pk=poi.pk)
    else:
        # Floor stock path: FIFO across available POIs, RECEIVED before CONFIRMED.
        # NOTE: Cannot use annotate_available_quantity() with select_for_update()
        # because PostgreSQL doesn't allow FOR UPDATE with GROUP BY clause.
        pois = (
            PurchaseOrderItem.objects.filter(
                order__destination_warehouse=allocation.stock.warehouse,
                product_variant=allocation.stock.product_variant,
                status__in=PurchaseOrderItemStatus.ACTIVE_STATUSES,
                quantity_ordered__gt=F("quantity_allocated"),
            )
            .select_for_update()
            .annotate(
                status_priority=Case(
                    When(
                        status=PurchaseOrderItemStatus.RECEIVED,
                        then=Value(0),
                    ),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("status_priority", "confirmed_at", "created_at")
        )

    remaining = quantity
    sources_to_update = {}  # POI ID -> AllocationSource
    pois_to_update = []

    # Get existing sources for this allocation to update them instead of creating duplicates
    existing_sources = {
        source.purchase_order_item_id: source
        for source in allocation.allocation_sources.select_for_update()
    }

    for poi in pois:
        available = poi.available_quantity
        assert available > 0, (
            "Despite checking available quantity > 0 in query poi has <0 available quantity"
        )

        consume = min(remaining, available)

        # Check if we already have a source for this POI - update it instead of creating new
        if poi.id in existing_sources:
            source = existing_sources[poi.id]
            source.quantity = F("quantity") + consume
            sources_to_update[poi.id] = source
        else:
            # Create new source
            source = AllocationSource(
                allocation=allocation,
                purchase_order_item=poi,
                quantity=consume,
            )
            sources_to_update[poi.id] = source

        # Update POI quantity_allocated
        poi.quantity_allocated = F("quantity_allocated") + consume
        pois_to_update.append(poi)
        remaining -= consume

        if remaining == 0:
            break

    if remaining > 0:
        raise InsufficientStock(
            [
                InsufficientStockData(
                    variant=allocation.stock.product_variant,
                    order_line=allocation.order_line,
                    available_quantity=quantity - remaining,
                )
            ]
        )

    # Save all sources (both new and updated)
    sources_to_create = []
    sources_to_save = []
    for _poi_id, source in sources_to_update.items():
        if source.pk:  # Existing source - update
            sources_to_save.append(source)
        else:  # New source - create
            sources_to_create.append(source)

    if sources_to_create:
        AllocationSource.objects.bulk_create(sources_to_create)
    if sources_to_save:
        AllocationSource.objects.bulk_update(sources_to_save, ["quantity"])
    if pois_to_update:
        PurchaseOrderItem.objects.bulk_update(pois_to_update, ["quantity_allocated"])


def allocate_sources(allocation: Allocation):
    """Create AllocationSources for the full allocation amount.

    Wrapper around _allocate_sources_incremental that allocates sources for
    the entire allocation.quantity_allocated using FIFO ordering of POIs.

    This is only used for free stock in an owned warehouse - confirming POs and moving stock from nonowned -> owned uses the PORA system.

    Args:
        allocation: The Allocation to create sources for (must be owned warehouse).

    Raises:
        InsufficientStock: If there are not enough POI batches.

    """
    return _allocate_sources_incremental(
        allocation=allocation, quantity=allocation.quantity_allocated
    )


@traced_atomic_transaction()
def allocate_stocks(
    order_lines_info: list["OrderLineInfo"],
    country_code: str,
    channel: "Channel",
    manager: PluginsManager,
    collection_point_pk: UUID | None = None,
    additional_filter_lookup: dict[str, Any] | None = None,
    check_reservations: bool = False,
    checkout_lines: Iterable["CheckoutLine"] | None = None,
):
    """Allocate stocks for given `order_lines` in given country.

    Function lock for update all stocks and allocations for variants in
    given country and order by pk. Next, generate the dictionary
    ({"stock_pk": "quantity_allocated"}) with actual allocated quantity for stocks.
    Iterate by stocks and allocate as many items as needed or available in stock
    for order line, until allocated all required quantity for the order line.
    If there is less quantity in stocks then rise InsufficientStock exception.

    """
    # allocation only applied to order lines with variants with track inventory
    # set to True
    order_lines_info = get_order_lines_with_track_inventory(order_lines_info)
    if not order_lines_info:
        return

    # Validate that we don't allocate more than what was ordered
    for line_info in order_lines_info:
        if line_info.quantity > line_info.line.quantity:
            raise AllocationQuantityError(
                line_info.line, line_info.quantity, line_info.line.quantity
            )

    channel_slug = channel.slug

    variants = [line_info.variant for line_info in order_lines_info]
    filter_lookup = {"product_variant__in": variants}

    if additional_filter_lookup is not None:
        filter_lookup.update(additional_filter_lookup)

    # in case of click and collect order, we need to check local or global stock
    # regardless of the country code
    stocks = (
        Stock.objects.for_channel_and_click_and_collect(channel_slug)
        if collection_point_pk
        else Stock.objects.for_channel_and_country(channel_slug, country_code)
    )

    stocks = list(
        stock_select_for_update_for_existing_qs(stocks)
        .filter(**filter_lookup)
        .values(
            "id",
            "product_variant",
            "pk",
            "quantity",
            "warehouse_id",
            "warehouse__is_owned",
        )
    )
    stocks_id = [stock.pop("id") for stock in stocks]

    quantity_reservation_for_stocks: dict = _prepare_stock_to_reserved_quantity_map(
        checkout_lines, check_reservations, stocks_id
    )

    quantity_allocation_list = list(
        Allocation.objects.filter(
            stock_id__in=stocks_id,
            quantity_allocated__gt=0,
        )
        .values("stock")
        .annotate(quantity_allocated_sum=Sum("quantity_allocated"))
    )
    quantity_allocation_for_stocks: dict = defaultdict(int)
    for allocation_data in quantity_allocation_list:
        quantity_allocation_for_stocks[allocation_data["stock"]] += allocation_data[
            "quantity_allocated_sum"
        ]

    stocks = sort_stocks(
        channel.allocation_strategy,
        stocks,
        channel,
        quantity_allocation_for_stocks,
        collection_point_pk,
    )

    variant_to_stocks: dict[int, list[StockData]] = defaultdict(list)
    for stock_data in stocks:
        variant = stock_data.pop("product_variant")
        variant_to_stocks[variant].append(StockData(**stock_data))

    insufficient_stock: list[InsufficientStockData] = []
    allocations: list[Allocation] = []
    for line_info in order_lines_info:
        line_info.variant = cast(ProductVariant, line_info.variant)
        stock_allocations = variant_to_stocks[line_info.variant.pk]
        insufficient_stock, allocation_items = _create_allocations(
            line_info,
            stock_allocations,
            quantity_allocation_for_stocks,
            quantity_reservation_for_stocks,
            insufficient_stock,
        )
        allocations.extend(allocation_items)

    if insufficient_stock:
        raise InsufficientStock(insufficient_stock)

    if allocations:
        Allocation.objects.bulk_create(allocations)

        # Fetch the allocations with their related stock objects
        # This is necessary because bulk_create doesn't populate relations
        stock_ids = {alloc.stock_id for alloc in allocations}
        order_line_ids = {alloc.order_line_id for alloc in allocations}
        allocations = list(
            Allocation.objects.filter(
                order_line_id__in=order_line_ids, stock_id__in=stock_ids
            ).select_related(
                "stock", "stock__warehouse", "stock__product_variant", "order_line"
            )
        )

        # Create AllocationSources for owned warehouses (batch tracking)
        # Get warehouse ownership info efficiently
        owned_stock_ids = set(
            Stock.objects.filter(
                id__in=stock_ids, warehouse__is_owned=True
            ).values_list("id", flat=True)
        )

        # Track orders to check for auto-confirmation
        orders_to_check = set()

        for allocation in allocations:
            if allocation.stock_id in owned_stock_ids:
                allocate_sources(allocation)
                # Check if order can be auto-confirmed after adding sources
                from ..order import OrderStatus

                if allocation.order_line.order.status == OrderStatus.UNCONFIRMED:
                    orders_to_check.add(allocation.order_line.order)

        # Auto-confirm orders that now have all allocations with sources
        # Only auto-confirm if channel setting allows it
        for order in orders_to_check:
            if channel.automatically_confirm_all_new_orders and can_confirm_order(
                order
            ):
                order.status = OrderStatus.UNFULFILLED
                order.save(update_fields=["status", "updated_at"])

                from ..order.actions import order_confirmed
                from ..plugins.manager import get_plugins_manager

                confirm_manager = get_plugins_manager(allow_replica=False)
                transaction.on_commit(
                    functools.partial(
                        order_confirmed,
                        order,
                        None,
                        None,
                        confirm_manager,
                        send_confirmation_email=True,
                    )
                )

        stocks_to_update_map = {alloc.stock_id: alloc.stock for alloc in allocations}
        quantity_from_allocations: dict[int, int] = defaultdict(int)

        for alloc in allocations:
            quantity_from_allocations[alloc.stock_id] += alloc.quantity_allocated

        for stock_id, quantity in quantity_from_allocations.items():
            stock = stocks_to_update_map[stock_id]
            stock.quantity_allocated = F("quantity_allocated") + quantity

        Stock.objects.bulk_update(stocks_to_update_map.values(), ["quantity_allocated"])

        for allocation in allocations:
            allocated_stock = (
                Allocation.objects.filter(stock_id=allocation.stock_id).aggregate(
                    Sum("quantity_allocated")
                )["quantity_allocated__sum"]
                or 0
            )
            if not max(allocation.stock.quantity - allocated_stock, 0):
                transaction.on_commit(
                    lambda: manager.product_variant_out_of_stock(allocation.stock)
                )


def _prepare_stock_to_reserved_quantity_map(
    checkout_lines, check_reservations, stocks_id
):
    """Prepare stock id to quantity reserved map for provided stock ids."""
    quantity_reservation_for_stocks: dict = defaultdict(int)

    if check_reservations:
        quantity_reservation = (
            Reservation.objects.filter(
                stock_id__in=stocks_id,
            )
            .not_expired()
            .exclude_checkout_lines(checkout_lines or [])
            .values("stock")
            .annotate(
                quantity_reserved=Coalesce(Sum("quantity_reserved"), 0),
            )
        )
        for reservation in quantity_reservation:
            quantity_reservation_for_stocks[reservation["stock"]] += reservation[
                "quantity_reserved"
            ]
    return quantity_reservation_for_stocks


def sort_stocks(
    allocation_strategy: str,
    stocks: list[dict],
    channel: "Channel",
    quantity_allocation_for_stocks: dict[int, int],
    collection_point_pk: UUID | None = None,
):
    """Sort stocks for allocation according to the specified strategy.

    IMPORTANT: Both strategies prioritize owned warehouses (is_owned=True) over
    non-owned warehouses. This ensures allocations use owned warehouse stock first,
    enabling proper batch tracking via PurchaseOrderItems and AllocationSources.

    Args:
        allocation_strategy: Either PRIORITIZE_HIGH_STOCK or PRIORITIZE_SORTING_ORDER
        stocks: List of stock dictionaries with warehouse__is_owned field
        channel: Channel with allocation strategy configuration
        quantity_allocation_for_stocks: Map of stock PK to allocated quantity
        collection_point_pk: Optional collection point warehouse (always prioritized)

    Returns:
        Sorted list of stocks (owned first, then strategy-specific sorting)

    """
    warehouse_ids = [stock_data["warehouse_id"] for stock_data in stocks]
    channel_warehouse_ids = ChannelWarehouse.objects.filter(
        channel_id=channel.id, warehouse_id__in=warehouse_ids
    ).values_list("warehouse_id", flat=True)

    def sort_stocks_by_highest_stocks(stock_data):
        """Sort the stocks by the highest quantity available.

        Priority (with reverse=True, highest first):
        1. Collection point (priority=2)
        2. Owned warehouses (priority=1, sorted by quantity desc)
        3. Non-owned warehouses (priority=0, sorted by quantity desc)
        """
        warehouse_id = stock_data.pop("warehouse_id")
        is_owned = stock_data.pop("warehouse__is_owned")

        available_quantity = stock_data[
            "quantity"
        ] - quantity_allocation_for_stocks.get(stock_data["pk"], 0)

        # Collection point gets highest priority
        if warehouse_id == collection_point_pk:
            return (2, math.inf)

        # Return tuple: (priority, quantity) for sorting with reverse=True
        # Owned=1, Non-owned=0, so owned comes first
        priority = 1 if is_owned else 0
        return (priority, available_quantity)

    def sort_stocks_by_warehouse_sorting_order(stock_data):
        """Sort the stocks based on the warehouse within channel order.

        Priority (with reverse=False, lowest first):
        1. Collection point (priority=-1)
        2. Owned warehouses (priority=0, sorted by channel order asc)
        3. Non-owned warehouses (priority=1, sorted by channel order asc)
        """
        sorted_warehouse_list = list(channel_warehouse_ids)
        warehouse_id = stock_data.pop("warehouse_id")
        is_owned = stock_data.pop("warehouse__is_owned")

        # Collection point gets highest priority (lowest value)
        if warehouse_id == collection_point_pk:
            return (-1, 0)

        # Return tuple: (priority, index) for sorting with reverse=False
        # Owned=0, Non-owned=1, so owned comes first
        priority = 0 if is_owned else 1
        return (priority, sorted_warehouse_list.index(warehouse_id))

    allocation_strategy_to_sort_method_and_reverse_option = {
        AllocationStrategy.PRIORITIZE_HIGH_STOCK: (sort_stocks_by_highest_stocks, True),
        AllocationStrategy.PRIORITIZE_SORTING_ORDER: (
            sort_stocks_by_warehouse_sorting_order,
            False,
        ),
    }
    sort_method, reverse = allocation_strategy_to_sort_method_and_reverse_option[
        allocation_strategy
    ]
    stocks.sort(key=sort_method, reverse=reverse)
    return stocks


def _create_allocations(
    line_info: "OrderLineInfo",
    stocks: list[StockData],
    stocks_allocations: dict,
    stocks_reservations: dict,
    insufficient_stock: list[InsufficientStockData],
) -> tuple[list[InsufficientStockData], list[Any]]:
    quantity = line_info.quantity
    quantity_allocated = 0
    allocations = []
    for stock_data in stocks:
        quantity_available_in_stock = stock_data.quantity
        quantity_available_in_stock -= stocks_allocations.get(stock_data.pk, 0)
        quantity_available_in_stock -= stocks_reservations.get(stock_data.pk, 0)

        quantity_to_allocate = min(
            (quantity - quantity_allocated), quantity_available_in_stock
        )
        if quantity_to_allocate > 0:
            allocations.append(
                Allocation(
                    order_line=line_info.line,
                    stock_id=stock_data.pk,
                    quantity_allocated=quantity_to_allocate,
                )
            )

            quantity_allocated += quantity_to_allocate
            if quantity_allocated == quantity:
                return insufficient_stock, allocations

    if not quantity_allocated == quantity:
        insufficient_stock.append(
            InsufficientStockData(
                variant=line_info.variant,
                order_line=line_info.line,
                available_quantity=0,
            )
        )
        return insufficient_stock, []
    return [], allocations


def deallocate_sources(allocation, quantity_to_deallocate, fulfillment_line=None):
    """Remove AllocationSources for an allocation and restore POI quantity_allocated.

    Args:
        allocation: The Allocation to deallocate sources from.
        quantity_to_deallocate: How much to deallocate (can be partial or full).
        fulfillment_line: Optional FulfillmentLine. If provided, creates FulfillmentSource
            records and increments POI.quantity_fulfilled. If None, this is a cancellation.

    Raises:
        ValueError: If order has items that have been shipped/fulfilled.

    """
    from ..inventory.models import PurchaseOrderItem
    from ..order import ORDER_ITEMS_SHIPPED_STATUS
    from .models import FulfillmentSource

    # SAFETY: Only allow deallocation for cancellations if items haven't left the warehouse
    # During fulfillment (when fulfillment_line is provided), deallocation is part of the
    # normal fulfillment flow, so we skip this check
    if fulfillment_line is None:
        order = allocation.order_line.order
        if order.status in ORDER_ITEMS_SHIPPED_STATUS:
            raise ValueError(
                f"Cannot deallocate from order {order.number} with status {order.status}. "
                f"Order has items that have been shipped/fulfilled."
            )

    # Get allocation sources in LIFO order (reverse of allocation - newest first)
    sources = allocation.allocation_sources.select_for_update().order_by("-pk")

    remaining = quantity_to_deallocate
    sources_to_delete = []
    sources_to_update = []
    pois_to_update_map = {}
    poi_deallocate_amounts = {}  # Track accumulated deallocation per POI
    poi_fulfill_amounts = {}  # Track accumulated fulfillment per POI
    fulfillment_sources_to_create = []

    for source in sources:
        if remaining <= 0:
            break

        deallocate_from_source = min(source.quantity, remaining)

        # Track POI updates - accumulate amounts for the same POI
        poi_id = source.purchase_order_item_id
        if poi_id not in pois_to_update_map:
            pois_to_update_map[poi_id] = source.purchase_order_item
            poi_deallocate_amounts[poi_id] = deallocate_from_source
            if fulfillment_line:
                poi_fulfill_amounts[poi_id] = deallocate_from_source
        else:
            # Same POI appears multiple times - accumulate the amounts
            poi_deallocate_amounts[poi_id] += deallocate_from_source
            if fulfillment_line:
                poi_fulfill_amounts[poi_id] += deallocate_from_source

        # Create FulfillmentSource if fulfilling (not cancelling)
        if fulfillment_line:
            fulfillment_sources_to_create.append(
                FulfillmentSource(
                    fulfillment_line=fulfillment_line,
                    purchase_order_item=source.purchase_order_item,
                    quantity=deallocate_from_source,
                )
            )

        if deallocate_from_source == source.quantity:
            # Fully deallocate this source
            sources_to_delete.append(source.id)
        else:
            # Partially deallocate
            source.quantity = F("quantity") - deallocate_from_source
            sources_to_update.append(source)

        remaining -= deallocate_from_source

    # Apply changes
    if fulfillment_sources_to_create:
        FulfillmentSource.objects.bulk_create(fulfillment_sources_to_create)
    if sources_to_delete:
        AllocationSource.objects.filter(id__in=sources_to_delete).delete()
    if sources_to_update:
        AllocationSource.objects.bulk_update(sources_to_update, ["quantity"])
    if pois_to_update_map:
        # Apply accumulated amounts to each POI using F() expressions
        for poi_id, poi in pois_to_update_map.items():
            poi.quantity_allocated = (
                F("quantity_allocated") - poi_deallocate_amounts[poi_id]
            )
            if fulfillment_line:
                poi.quantity_fulfilled = (
                    F("quantity_fulfilled") + poi_fulfill_amounts[poi_id]
                )

        update_fields = ["quantity_allocated"]
        if fulfillment_line:
            update_fields.append("quantity_fulfilled")
        PurchaseOrderItem.objects.bulk_update(
            pois_to_update_map.values(), update_fields
        )


def deallocate_stock(
    order_lines_data: list["OrderLineInfo"],
    manager: PluginsManager,
    fulfillment_line_map: dict | None = None,
):
    """Deallocate stocks for given `order_lines`.

    Function lock for update stocks and allocations related to given `order_lines`.
    Iterate over allocations sorted by `stock.pk` and deallocate as many items
    as needed of available in stock for order line, until deallocated all required
    quantity for the order line. If there is less quantity in stocks then
    raise an exception.

    Args:
        order_lines_data: List of OrderLineInfo objects containing order lines
            and related information for deallocation.
        manager: PluginsManager instance for handling plugin hooks.
        fulfillment_line_map: Optional dict mapping (order_line_id, warehouse_id) to
            FulfillmentLine. When provided, creates FulfillmentSource audit trail.

    """
    lines = [line_info.line for line_info in order_lines_data]
    lines_allocations = allocation_with_stock_qs_select_for_update().filter(
        order_line__in=lines
    )

    line_to_allocations: dict[UUID, list[Allocation]] = defaultdict(list)
    for allocation in lines_allocations:
        line_to_allocations[allocation.order_line_id].append(allocation)

    allocations_to_update = []
    stocks_to_update = []
    not_dellocated_lines = []
    for line_info in order_lines_data:
        order_line = line_info.line
        quantity = line_info.quantity
        allocations = line_to_allocations[order_line.pk]
        quantity_dealocated = 0
        for allocation in allocations:
            quantity_to_deallocate = min(
                (quantity - quantity_dealocated), allocation.quantity_allocated
            )
            if quantity_to_deallocate > 0:
                # Deallocate sources for owned warehouses (batch tracking)
                if allocation.stock.warehouse.is_owned:
                    # Look up FulfillmentLine if this is a fulfillment (not cancellation)
                    fulfillment_line = None
                    if fulfillment_line_map:
                        fulfillment_line = fulfillment_line_map.get(
                            (allocation.order_line_id, allocation.stock.warehouse_id)
                        )
                    deallocate_sources(
                        allocation, quantity_to_deallocate, fulfillment_line
                    )

                allocation.quantity_allocated = (
                    allocation.quantity_allocated - quantity_to_deallocate
                )
                stock = allocation.stock
                stock.quantity_allocated = (
                    F("quantity_allocated") - quantity_to_deallocate
                )
                stocks_to_update.append(stock)
                quantity_dealocated += quantity_to_deallocate
                allocations_to_update.append(allocation)
                if quantity_dealocated == quantity:
                    break
        if not quantity_dealocated == quantity:
            not_dellocated_lines.append(order_line)

    allocations_before_update = list(
        Allocation.objects.filter(
            id__in=[a.id for a in allocations_to_update]
        ).annotate_stock_available_quantity()
    )

    Allocation.objects.bulk_update(allocations_to_update, ["quantity_allocated"])

    for allocation_before_update in allocations_before_update:
        available_stock_now = Allocation.objects.available_quantity_for_stock(
            allocation_before_update.stock
        )
        if (
            allocation_before_update.stock_available_quantity <= 0
            and available_stock_now > 0
        ):
            transaction.on_commit(
                lambda: manager.product_variant_back_in_stock(
                    allocation_before_update.stock
                )
            )

    Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])

    if not_dellocated_lines:
        raise AllocationError(not_dellocated_lines)


@traced_atomic_transaction()
def increase_stock(
    order_line: OrderLine,
    warehouse: Warehouse,
    quantity: int,
    allocate: bool = False,
):
    """Increse stock quantity for given `order_line` in a given warehouse.

    Function lock for update stock and allocations related to given `order_line`
    in a given warehouse. If the stock exists, increase the stock quantity
    by given value. If not exist create a stock with the given quantity. This function
    can create the allocation for increased quantity in stock by passing True
    to `allocate` argument. If the order line has the allocation in this stock
    function increase `quantity_allocated`. If allocation does not exist function
    create a new allocation for this order line in this stock.
    """
    assert order_line.variant
    stock = (
        stock_qs_select_for_update()
        .filter(warehouse=warehouse, product_variant=order_line.variant)
        .first()
    )
    if stock:
        stock.increase_stock(quantity, commit=True)
    else:
        stock = Stock.objects.create(
            warehouse=warehouse, product_variant=order_line.variant, quantity=quantity
        )
    if allocate:
        allocation = order_line.allocations.filter(stock=stock).first()
        if allocation:
            # Increase existing allocation
            allocation.quantity_allocated = F("quantity_allocated") + quantity
            allocation.save(update_fields=["quantity_allocated"])
            # Allocate sources for the increased quantity (owned warehouses only)
            if stock.warehouse.is_owned:
                allocation.refresh_from_db()
                # Allocate sources for just the incremental quantity
                _allocate_sources_incremental(allocation, quantity)
        else:
            # Create new allocation
            allocation = Allocation.objects.create(
                order_line=order_line, stock=stock, quantity_allocated=quantity
            )
            # Allocate sources for owned warehouses
            if stock.warehouse.is_owned:
                allocate_sources(allocation)

        stock.quantity_allocated = F("quantity_allocated") + quantity
        stock.save(update_fields=["quantity_allocated"])


def _reduce_quantity_allocated_for_stocks(
    allocations: Iterable[Allocation],
) -> list[Stock]:
    """Reduce quantity allocated for stocks from allocations.

    This function reduces the quantity allocated for stocks based on the allocations
    associated with them. It takes a list of Allocation objects and returns a list of
    Stock objects with their quantity_allocated field updated.
    """
    stocks_to_update_map: dict[int, Stock] = {
        alloc.stock_id: alloc.stock for alloc in allocations
    }
    quantity_allocated_to_reduce: dict[int, int] = defaultdict(int)
    for alloc in allocations:
        quantity_allocated_to_reduce[alloc.stock_id] += alloc.quantity_allocated

    for stock_pk, quantity_allocated in quantity_allocated_to_reduce.items():
        stock = stocks_to_update_map[stock_pk]
        stock.quantity_allocated = F("quantity_allocated") - quantity_allocated
    return list(stocks_to_update_map.values())


@traced_atomic_transaction()
def increase_allocations(
    lines_info: list["OrderLineInfo"], channel: "Channel", manager: PluginsManager
):
    """Increase allocation for order lines with appropriate quantity."""
    line_pks = [info.line.pk for info in lines_info]
    allocations = list(
        allocation_with_stock_qs_select_for_update()
        .select_related("order_line")
        .filter(order_line__in=line_pks)
    )

    # evaluate allocations query to trigger select_for_update lock
    allocation_pks_to_delete = [alloc.pk for alloc in allocations]
    allocation_quantity_map: dict[UUID, list] = defaultdict(list)

    for alloc in allocations:
        allocation_quantity_map[alloc.order_line.pk].append(alloc.quantity_allocated)

    for line_info in lines_info:
        allocated = sum(allocation_quantity_map[line_info.line.pk])
        # line_info.quantity resembles amount to add, sum it with already allocated.
        line_info.quantity += allocated

    # Reduces quantity allocated for stocks from allocations, as `allocate_stocks`
    # will create new allocations.
    stocks_to_update = _reduce_quantity_allocated_for_stocks(allocations=allocations)

    Allocation.objects.filter(pk__in=allocation_pks_to_delete).delete()
    Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])

    order = lines_info[0].line.order
    country_code = get_active_country(
        channel, order.shipping_address, order.billing_address
    )
    allowed_warehouse_ids = list(order.allowed_warehouses.values_list("id", flat=True))
    additional_filter_lookup = (
        {"warehouse_id__in": allowed_warehouse_ids} if allowed_warehouse_ids else None
    )
    allocate_stocks(
        lines_info,
        country_code,
        channel,
        manager,
        additional_filter_lookup=additional_filter_lookup,
    )


def decrease_allocations(
    lines_info: list["OrderLineInfo"], manager, fulfillment_line_map: dict | None = None
):
    """Decrease allocations for provided order lines."""
    lines_to_deallocate = get_order_lines_to_deallocate(lines_info)
    if not lines_to_deallocate:
        return
    try:
        deallocate_stock(lines_info, manager, fulfillment_line_map)
    except AllocationError as exc:
        # Deallocate sources before zeroing allocations
        allocations = list(
            Allocation.objects.order_by("stock_id")
            .select_related("stock__warehouse")
            .filter(order_line__in=exc.order_lines)
        )
        for allocation in allocations:
            if allocation.stock.warehouse.is_owned:
                # Look up FulfillmentLine if this is a fulfillment (not cancellation)
                fulfillment_line = None
                if fulfillment_line_map:
                    fulfillment_line = fulfillment_line_map.get(
                        (allocation.order_line_id, allocation.stock.warehouse_id)
                    )
                deallocate_sources(
                    allocation, allocation.quantity_allocated, fulfillment_line
                )

        Allocation.objects.filter(id__in=[a.id for a in allocations]).update(
            quantity_allocated=0
        )


@traced_atomic_transaction()
def decrease_stock(
    order_lines_info: list["OrderLineInfo"],
    manager,
    allow_stock_to_be_exceeded: bool = False,
    fulfillment_line_map: dict | None = None,
):
    """Decrease stocks quantities for given `order_lines` in given warehouses.

    Function deallocate as many quantities as requested if order_line has less quantity
    from requested function deallocate whole quantity. Next function try to find the
    stock in a given warehouse, if stock not exists or have not enough stock,
    the function raise InsufficientStock exception. When the stock has enough quantity
    function decrease it by given value.
    If allow_stock_to_be_exceeded flag is True then quantity could be < 0.

    Args:
        order_lines_info: List of OrderLineInfo objects containing order lines
            and warehouse information for stock decrease.
        manager: PluginsManager instance for handling plugin hooks.
        allow_stock_to_be_exceeded: If True, allows stock quantity to go below zero.
        fulfillment_line_map: Optional dict mapping (order_line_id, warehouse_id) to
            FulfillmentLine. When provided, creates FulfillmentSource audit trail.

    """
    decrease_allocations(order_lines_info, manager, fulfillment_line_map)

    order_lines_info = get_order_lines_with_track_inventory(order_lines_info)
    if not order_lines_info:
        return
    variants = [line_info.variant for line_info in order_lines_info]
    warehouse_pks = [line_info.warehouse_pk for line_info in order_lines_info]

    stocks = (
        stock_qs_select_for_update()
        .filter(product_variant__in=variants)
        .filter(warehouse_id__in=warehouse_pks)
        .select_related("product_variant", "warehouse")
    )

    variant_and_warehouse_to_stock: dict[int, dict[UUID, Stock]] = defaultdict(dict)
    for stock in stocks:
        variant_and_warehouse_to_stock[stock.product_variant_id][stock.warehouse_id] = (
            stock
        )

    quantity_allocation_list = list(
        Allocation.objects.filter(
            stock__in=stocks,
            quantity_allocated__gt=0,
        )
        .values("stock")
        .annotate(Sum("quantity_allocated"))
    )

    quantity_allocation_for_stocks: dict[int, int] = defaultdict(int)
    for allocation in quantity_allocation_list:
        quantity_allocation_for_stocks[allocation["stock"]] += allocation[
            "quantity_allocated__sum"
        ]
    _decrease_stocks_quantity(
        order_lines_info,
        variant_and_warehouse_to_stock,
        quantity_allocation_for_stocks,
        allow_stock_to_be_exceeded,
    )

    stock_ids = (s.id for s in stocks)
    for stock in Stock.objects.filter(id__in=stock_ids).annotate_available_quantity():
        if stock.available_quantity <= 0:
            transaction.on_commit(lambda: manager.product_variant_out_of_stock(stock))


def _decrease_stocks_quantity(
    order_lines_info: list["OrderLineInfo"],
    variant_and_warehouse_to_stock: dict[int, dict[UUID, Stock]],
    quantity_allocation_for_stocks: dict[int, int],
    allow_stock_to_be_exceeded: bool = False,
):
    insufficient_stocks: list[InsufficientStockData] = []
    stocks_to_update = []
    for line_info in order_lines_info:
        variant = line_info.variant
        if not variant:
            continue
        warehouse_pk = line_info.warehouse_pk
        stock = (
            variant_and_warehouse_to_stock.get(variant.pk, {}).get(warehouse_pk)
            if warehouse_pk
            else None
        )
        if stock is None:
            # If there is no stock but allow_stock_to_be_exceeded == True
            # we proceed with fulfilling the order, treat as error otherwise
            if not allow_stock_to_be_exceeded:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant=variant,
                        order_line=line_info.line,
                        warehouse_pk=warehouse_pk,
                        available_quantity=0,
                    )
                )
            continue

        quantity_allocated = quantity_allocation_for_stocks.get(stock.pk, 0)

        is_stock_exceeded = stock.quantity - quantity_allocated < line_info.quantity
        if is_stock_exceeded and not allow_stock_to_be_exceeded:
            insufficient_stocks.append(
                InsufficientStockData(
                    variant=variant,
                    order_line=line_info.line,
                    warehouse_pk=warehouse_pk,
                    available_quantity=0,
                )
            )
            continue
        stock.quantity = stock.quantity - line_info.quantity
        stocks_to_update.append(stock)

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)

    Stock.objects.bulk_update(stocks_to_update, ["quantity"])


def _get_variant_for_order_line_info(
    order_line_info: OrderLineInfo,
) -> ProductVariant | None:
    variant = order_line_info.variant
    if not variant and order_line_info.line.variant_id:
        variant = order_line_info.line.variant
        order_line_info.variant = variant
    return variant


def get_order_lines_with_track_inventory(
    order_lines_info: list["OrderLineInfo"],
) -> list["OrderLineInfo"]:
    """Return order lines with variants with track inventory set to True."""
    lines_to_return = []
    for line_info in order_lines_info:
        variant = _get_variant_for_order_line_info(line_info)

        if not variant:
            continue
        if variant.is_preorder_active():
            continue
        if not variant.track_inventory:
            continue
        lines_to_return.append(line_info)
    return lines_to_return


def get_order_lines_to_deallocate(
    order_lines_info: list["OrderLineInfo"],
) -> list["OrderLineInfo"]:
    """Get order lines to deallocate.

    The function returns the lines with active track inventory and the lines where track
    inventory was turned off but for some reason the allocations are present.
    Case like turning on & off the track-inventory.
    """
    order_lines_info_map = {
        line_info.line.id: line_info for line_info in order_lines_info
    }

    lines_to_deallocate = []
    existing_allocations = Allocation.objects.filter(
        order_line_id__in=order_lines_info_map.keys(),
    )
    for allocation in existing_allocations:
        line_to_deallocate = order_lines_info_map.get(allocation.order_line_id)
        if line_to_deallocate is None:
            continue
        _get_variant_for_order_line_info(line_to_deallocate)
        lines_to_deallocate.append(line_to_deallocate)

    return lines_to_deallocate


@traced_atomic_transaction()
def deallocate_stock_for_orders(orders_ids: list[UUID], manager: PluginsManager):
    """Remove all allocations for given orders."""
    lines = OrderLine.objects.filter(order_id__in=orders_ids)
    allocations = list(
        allocation_with_stock_qs_select_for_update()
        .select_related("stock__warehouse")
        .filter(
            Exists(lines.filter(id=OuterRef("order_line_id"))),
            quantity_allocated__gt=0,
        )
    )

    # Deallocate sources for owned warehouses
    for allocation in allocations:
        if allocation.stock.warehouse.is_owned:
            deallocate_sources(allocation, allocation.quantity_allocated)

    stocks_to_update = _reduce_quantity_allocated_for_stocks(allocations)

    allocations_for_back_in_stock = Allocation.objects.filter(
        id__in=[allocation.id for allocation in allocations]
    )
    for allocation in allocations_for_back_in_stock.annotate_stock_available_quantity():
        if allocation.stock_available_quantity <= 0:
            transaction.on_commit(
                lambda: manager.product_variant_back_in_stock(allocation.stock)
            )

    Allocation.objects.filter(id__in=[a.id for a in allocations]).delete()
    Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])


@traced_atomic_transaction()
def allocate_preorders(
    order_lines_info: list["OrderLineInfo"],
    channel_slug: str,
    check_reservations: bool = False,
    checkout_lines: Iterable["CheckoutLine"] | None = None,
):
    """Allocate preorder variant for given `order_lines` in given channel."""
    order_lines_info = get_order_lines_with_preorder(order_lines_info)
    if not order_lines_info:
        return

    variants = [line_info.variant for line_info in order_lines_info]

    all_variants_channel_listings = (
        ProductVariantChannelListing.objects.filter(variant__in=variants)
        .select_for_update(of=("self",))
        .select_related("channel")
        .values("id", "channel__slug", "preorder_quantity_threshold", "variant_id")
    )
    all_variants_channel_listings_id = [
        channel_listing["id"] for channel_listing in all_variants_channel_listings
    ]

    quantity_allocation_list = list(
        PreorderAllocation.objects.filter(
            product_variant_channel_listing_id__in=all_variants_channel_listings_id,  # noqa: E501
            quantity__gt=0,
        )
        .values("product_variant_channel_listing")
        .annotate(preorder_quantity_allocated=Sum("quantity"))
    )
    quantity_allocation_for_channel: dict = defaultdict(int)
    for allocation in quantity_allocation_list:
        quantity_allocation_for_channel[
            allocation["product_variant_channel_listing"]
        ] = allocation["preorder_quantity_allocated"]

    variants_to_channel_listings = {
        channel_listing["variant_id"]: (
            channel_listing["id"],
            channel_listing["preorder_quantity_threshold"],
        )
        for channel_listing in all_variants_channel_listings
        if channel_listing["channel__slug"] == channel_slug
    }

    variants_channel_listings = defaultdict(list)
    for channel_listing in all_variants_channel_listings:
        variants_channel_listings[channel_listing["variant_id"]].append(
            channel_listing["id"]
        )

    if check_reservations:
        quantity_reservation_list = (
            PreorderReservation.objects.filter(
                product_variant_channel_listing_id__in=all_variants_channel_listings_id,  # noqa: E501
                quantity_reserved__gt=0,
            )
            .not_expired()
            .exclude_checkout_lines(checkout_lines)
            .values("product_variant_channel_listing")
            .annotate(quantity_reserved_sum=Sum("quantity_reserved"))
        )
        listings_reservations: dict = defaultdict(int)
        for reservation in quantity_reservation_list:
            listings_reservations[reservation["product_variant_channel_listing"]] += (
                reservation["quantity_reserved_sum"]
            )
    else:
        listings_reservations = defaultdict(int)

    variants_global_allocations: dict[int, int] = defaultdict(int)
    for channel_listing in all_variants_channel_listings:
        variants_global_allocations[channel_listing["variant_id"]] += (
            quantity_allocation_for_channel[channel_listing["id"]]
        )

    insufficient_stocks: list[InsufficientStockData] = []
    allocations: list[PreorderAllocation] = []
    for line_info in order_lines_info:
        variant = cast(ProductVariant, line_info.variant)
        allocation_item, insufficient_stock = _create_preorder_allocation(
            line_info,
            variants_to_channel_listings[variant.id],
            variants_global_allocations[variant.id],
            variants_channel_listings[variant.id],
            quantity_allocation_for_channel,
            listings_reservations,
        )
        if allocation_item:
            allocations.append(allocation_item)
        if insufficient_stock:
            insufficient_stocks.append(insufficient_stock)

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)

    if allocations:
        PreorderAllocation.objects.bulk_create(allocations)


def get_order_lines_with_preorder(
    order_lines_info: list["OrderLineInfo"],
) -> list["OrderLineInfo"]:
    """Return order lines with variants with preorder flag set to True."""
    return [
        line_info
        for line_info in order_lines_info
        if line_info.variant and line_info.variant.is_preorder_active()
    ]


def _create_preorder_allocation(
    line_info: "OrderLineInfo",
    variant_channel_data: tuple[int, int | None],
    variant_global_allocation: int,
    variants_channel_listings: list[int],
    quantity_allocation_for_channel: dict[int, int],
    listings_reservations: dict[int, int],
) -> tuple[PreorderAllocation | None, InsufficientStockData | None]:
    variant = cast(ProductVariant, line_info.variant)
    quantity = line_info.quantity
    channel_listing_id, channel_quantity_threshold = variant_channel_data

    if channel_quantity_threshold is not None:
        channel_availability = channel_quantity_threshold
        channel_availability -= quantity_allocation_for_channel[channel_listing_id]
        channel_availability -= listings_reservations[channel_listing_id]
        channel_availability = max(channel_availability, 0)

        if quantity > channel_availability:
            return None, InsufficientStockData(
                variant=variant,
                available_quantity=channel_availability,
            )

    if variant.preorder_global_threshold is not None:
        global_availability = variant.preorder_global_threshold
        global_availability -= variant_global_allocation
        for listing_id in variants_channel_listings:
            global_availability -= listings_reservations[listing_id]
        global_availability = max(global_availability, 0)

        if quantity > global_availability:
            return None, InsufficientStockData(
                variant=variant, available_quantity=global_availability
            )

    return (
        PreorderAllocation(
            order_line=line_info.line,
            product_variant_channel_listing_id=channel_listing_id,
            quantity=quantity,
        ),
        None,
    )


@traced_atomic_transaction()
def deactivate_preorder_for_variant(product_variant: ProductVariant):
    """Complete preorder for product variant.

    All preorder settings should be cleared and all preorder allocations
    should be replaced by regular allocations.
    """
    if not product_variant.is_preorder:
        return
    channel_listings = ProductVariantChannelListing.objects.filter(
        variant_id=product_variant.pk
    )
    channel_listings_pk = (channel_listing.id for channel_listing in channel_listings)
    preorder_allocations = (
        PreorderAllocation.objects.filter(
            product_variant_channel_listing_id__in=channel_listings_pk
        )
        .select_for_update(of=("self",))
        .select_related("order_line", "order_line__order")
    )

    allocations_to_create = []
    stocks_to_create = []
    stocks_to_update = []
    for preorder_allocation in preorder_allocations:
        stock = _get_stock_for_preorder_allocation(preorder_allocation, product_variant)
        if stock._state.adding:
            stock.quantity_allocated += preorder_allocation.quantity
            stocks_to_create.append(stock)
        else:
            stock.quantity_allocated = (
                F("quantity_allocated") + preorder_allocation.quantity
            )
            stocks_to_update.append(stock)
        allocations_to_create.append(
            Allocation(
                order_line=preorder_allocation.order_line,
                stock=stock,
                quantity_allocated=preorder_allocation.quantity,
            )
        )

    if stocks_to_create:
        Stock.objects.bulk_create(stocks_to_create)

    if stocks_to_update:
        Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])

    if allocations_to_create:
        Allocation.objects.bulk_create(allocations_to_create)

        # Create AllocationSources for owned warehouses
        for allocation in allocations_to_create:
            if allocation.stock.warehouse.is_owned:
                allocate_sources(allocation)

    if preorder_allocations:
        preorder_allocations.delete()

    product_variant.preorder_global_threshold = None
    product_variant.preorder_end_date = None
    product_variant.is_preorder = False
    product_variant.save(
        update_fields=[
            "preorder_global_threshold",
            "preorder_end_date",
            "is_preorder",
            "updated_at",
        ]
    )

    ProductVariantChannelListing.objects.filter(variant_id=product_variant.pk).update(
        preorder_quantity_threshold=None
    )


def _get_stock_for_preorder_allocation(
    preorder_allocation: PreorderAllocation, product_variant: ProductVariant
) -> Stock:
    """Return stock where preordered variant should be allocated.

    By default this function uses any warehouse from the shipping zone that matches
    order's shipping method. If order has no shipping method set, it uses any warehouse
    that matches order's country. Function returns existing stock for selected warehouse
    or creates a new one unsaved `Stock` instance. Function raises an error if there is
    no warehouse assigned to any shipping zone handles order's country.
    """
    order = preorder_allocation.order_line.order
    shipping_method_id = order.shipping_method_id

    if shipping_method_id is not None:
        warehouse = Warehouse.objects.filter(
            shipping_zones__id=order.shipping_method.shipping_zone_id  # type: ignore[union-attr]
        ).first()
    else:
        from ..order.utils import get_order_country

        country = get_order_country(order)
        warehouse = Warehouse.objects.filter(
            shipping_zones__countries__contains=country
        ).first()

    if not warehouse:
        raise PreorderAllocationError(preorder_allocation.order_line)

    stock = list(
        stock_qs_select_for_update().filter(
            warehouse=warehouse, product_variant=product_variant
        )
    )

    return (stock[0] if stock else None) or Stock(
        warehouse=warehouse, product_variant=product_variant, quantity=0
    )
