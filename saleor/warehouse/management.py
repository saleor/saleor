import math
from collections import defaultdict, namedtuple
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, cast

from django.db import transaction
from django.db.models import F, Sum
from django.db.models.expressions import Exists, OuterRef
from django.db.models.functions import Coalesce

from ..channel import AllocationStrategy
from ..checkout.models import CheckoutLine
from ..core.exceptions import (
    AllocationError,
    InsufficientStock,
    InsufficientStockData,
    PreorderAllocationError,
)
from ..core.tracing import traced_atomic_transaction
from ..order.fetch import OrderLineInfo
from ..order.models import OrderLine
from ..plugins.manager import PluginsManager
from ..product.models import ProductVariant, ProductVariantChannelListing
from .models import (
    Allocation,
    ChannelWarehouse,
    PreorderAllocation,
    PreorderReservation,
    Reservation,
    Stock,
    Warehouse,
)

if TYPE_CHECKING:
    from uuid import UUID

    from ..channel.models import Channel
    from ..order.models import Order


StockData = namedtuple("StockData", ["pk", "quantity"])


@traced_atomic_transaction()
def allocate_stocks(
    order_lines_info: Iterable["OrderLineInfo"],
    country_code: str,
    channel: "Channel",
    manager: PluginsManager,
    collection_point_pk: Optional[str] = None,
    additional_filter_lookup: Optional[Dict[str, Any]] = None,
    check_reservations: bool = False,
    checkout_lines: Optional[Iterable["CheckoutLine"]] = None,
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
        stocks.select_for_update(of=("self",))
        .filter(**filter_lookup)
        .order_by("pk")
        .values("id", "product_variant", "pk", "quantity", "warehouse_id")
    )
    stocks_id = (stock.pop("id") for stock in stocks)

    quantity_reservation_for_stocks: Dict = _prepare_stock_to_reserved_quantity_map(
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
    quantity_allocation_for_stocks: Dict = defaultdict(int)
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

    variant_to_stocks: Dict[int, List[StockData]] = defaultdict(list)
    for stock_data in stocks:
        variant = stock_data.pop("product_variant")
        variant_to_stocks[variant].append(StockData(**stock_data))

    insufficient_stock: List[InsufficientStockData] = []
    allocations: List[Allocation] = []
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
        stocks_to_update = []
        for alloc in Allocation.objects.bulk_create(allocations):
            stock = alloc.stock
            stock.quantity_allocated = (
                F("quantity_allocated") + alloc.quantity_allocated
            )
            stocks_to_update.append(stock)
        Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])

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
    quantity_reservation_for_stocks: Dict = defaultdict(int)

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
        )  # type: ignore
        for reservation in quantity_reservation:
            quantity_reservation_for_stocks[reservation["stock"]] += reservation[
                "quantity_reserved"
            ]
    return quantity_reservation_for_stocks


def sort_stocks(
    allocation_strategy: str,
    stocks: List[dict],
    channel: "Channel",
    quantity_allocation_for_stocks: Dict[int, int],
    collection_point_pk: Optional[str] = None,
):
    warehouse_ids = [stock_data["warehouse_id"] for stock_data in stocks]
    channel_warehouse_ids = ChannelWarehouse.objects.filter(
        channel_id=channel.id, warehouse_id__in=warehouse_ids
    ).values_list("warehouse_id", flat=True)

    def sort_stocks_by_highest_stocks(stock_data):
        """Sort the stocks by the highest quantity available."""
        # in case of click and collect order we should allocate stocks from
        # collection point warehouse at the first place
        if stock_data.pop("warehouse_id") == collection_point_pk:
            return math.inf
        return stock_data["quantity"] - quantity_allocation_for_stocks.get(
            stock_data["pk"], 0
        )

    def sort_stocks_by_warehouse_sorting_order(stock_data):
        """Sort the stocks based on the warehouse within channel order."""
        # get the sort order for stocks warehouses within the channel
        sorted_warehouse_list = list(channel_warehouse_ids)

        warehouse_id = stock_data.pop("warehouse_id")
        # in case of click and collect order we should allocate stocks from
        # collection point warehouse at the first place
        if warehouse_id == collection_point_pk:
            return -math.inf
        return sorted_warehouse_list.index(warehouse_id)

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
    stocks: List[StockData],
    stocks_allocations: dict,
    stocks_reservations: dict,
    insufficient_stock: List[InsufficientStockData],
):
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
                variant=line_info.variant, order_line=line_info.line  # type: ignore
            )
        )
        return insufficient_stock, []


def deallocate_stock(
    order_lines_data: Iterable["OrderLineInfo"], manager: PluginsManager
):
    """Deallocate stocks for given `order_lines`.

    Function lock for update stocks and allocations related to given `order_lines`.
    Iterate over allocations sorted by `stock.pk` and deallocate as many items
    as needed of available in stock for order line, until deallocated all required
    quantity for the order line. If there is less quantity in stocks then
    raise an exception.
    """
    lines = [line_info.line for line_info in order_lines_data]
    lines_allocations = (
        Allocation.objects.filter(order_line__in=lines)
        .select_related("stock")
        .select_for_update(
            of=(
                "self",
                "stock",
            )
        )
        .order_by("stock__pk")
    )

    line_to_allocations: Dict["UUID", List[Allocation]] = defaultdict(list)
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
        Stock.objects.select_for_update(of=("self",))
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
            allocation.quantity_allocated = F("quantity_allocated") + quantity
            allocation.save(update_fields=["quantity_allocated"])
        else:
            Allocation.objects.create(
                order_line=order_line, stock=stock, quantity_allocated=quantity
            )
        stock.quantity_allocated = F("quantity_allocated") + quantity
        stock.save(update_fields=["quantity_allocated"])


@traced_atomic_transaction()
def increase_allocations(
    lines_info: Iterable["OrderLineInfo"], channel: "Channel", manager: PluginsManager
):
    """Increase allocation for order lines with appropriate quantity."""
    line_pks = [info.line.pk for info in lines_info]
    allocations = list(
        Allocation.objects.filter(order_line__in=line_pks)
        .select_related("stock", "order_line")
        .select_for_update(of=("self", "stock"))
    )
    # evaluate allocations query to trigger select_for_update lock
    allocation_pks_to_delete = [alloc.pk for alloc in allocations]
    allocation_quantity_map: Dict["UUID", list] = defaultdict(list)

    for alloc in allocations:
        allocation_quantity_map[alloc.order_line.pk].append(alloc.quantity_allocated)

    for line_info in lines_info:
        allocated = sum(allocation_quantity_map[line_info.line.pk])
        # line_info.quantity resembles amount to add, sum it with already allocated.
        line_info.quantity += allocated

    stocks_to_update = []
    for alloc in allocations:
        stock = alloc.stock
        stock.quantity_allocated = F("quantity_allocated") - alloc.quantity_allocated
        stocks_to_update.append(stock)
    Allocation.objects.filter(pk__in=allocation_pks_to_delete).delete()
    Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])

    allocate_stocks(
        lines_info,
        lines_info[0].line.order.shipping_address.country.code,  # type: ignore
        channel,
        manager,
    )


def decrease_allocations(lines_info: Iterable["OrderLineInfo"], manager):
    """Decreate allocations for provided order lines."""
    tracked_lines = get_order_lines_with_track_inventory(lines_info)
    if not tracked_lines:
        return
    decrease_stock(tracked_lines, update_stocks=False, manager=manager)


@traced_atomic_transaction()
def decrease_stock(
    order_lines_info: Iterable["OrderLineInfo"],
    manager,
    update_stocks=True,
    allow_stock_to_be_exceeded: bool = False,
):
    """Decrease stocks quantities for given `order_lines` in given warehouses.

    Function deallocate as many quantities as requested if order_line has less quantity
    from requested function deallocate whole quantity. Next function try to find the
    stock in a given warehouse, if stock not exists or have not enough stock,
    the function raise InsufficientStock exception. When the stock has enough quantity
    function decrease it by given value.
    If update_stocks is False, allocations will decrease but stocks quantities
    will stay unmodified (case of unconfirmed order editing).
    If allow_stock_to_be_exceeded flag is True then quantity could be < 0.
    """
    variants = [line_info.variant for line_info in order_lines_info]
    warehouse_pks = [line_info.warehouse_pk for line_info in order_lines_info]
    try:
        deallocate_stock(order_lines_info, manager)
    except AllocationError as exc:
        Allocation.objects.filter(order_line__in=exc.order_lines).update(
            quantity_allocated=0
        )

    stocks = (
        Stock.objects.select_for_update(of=("self",))
        .filter(product_variant__in=variants)
        .filter(warehouse_id__in=warehouse_pks)
        .select_related("product_variant", "warehouse")
        .order_by("pk")
    )

    variant_and_warehouse_to_stock: Dict[int, Dict[str, Stock]] = defaultdict(dict)
    for stock in stocks:
        variant_and_warehouse_to_stock[stock.product_variant_id][
            str(stock.warehouse_id)
        ] = stock

    quantity_allocation_list = list(
        Allocation.objects.filter(
            stock__in=stocks,
            quantity_allocated__gt=0,
        )
        .values("stock")
        .annotate(Sum("quantity_allocated"))
    )

    if update_stocks:
        quantity_allocation_for_stocks: Dict[int, int] = defaultdict(int)
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
        for stock in Stock.objects.filter(
            id__in=stock_ids
        ).annotate_available_quantity():
            if stock.available_quantity <= 0:
                transaction.on_commit(
                    lambda: manager.product_variant_out_of_stock(stock)
                )


def _decrease_stocks_quantity(
    order_lines_info: Iterable["OrderLineInfo"],
    variant_and_warehouse_to_stock: Dict[int, Dict[str, Stock]],
    quantity_allocation_for_stocks: Dict[int, int],
    allow_stock_to_be_exceeded: bool = False,
):
    insufficient_stocks: List[InsufficientStockData] = []
    stocks_to_update = []
    for line_info in order_lines_info:
        variant = line_info.variant
        warehouse_pk = str(line_info.warehouse_pk)
        stock = variant_and_warehouse_to_stock.get(variant.pk, {}).get(  # type: ignore
            warehouse_pk
        )
        if stock is None:
            # If there is no stock but allow_stock_to_be_exceeded == True
            # we proceed with fulfilling the order, treat as error otherwise
            if not allow_stock_to_be_exceeded:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant, line_info.line, warehouse_pk  # type: ignore
                    )
                )
            continue

        quantity_allocated = quantity_allocation_for_stocks.get(stock.pk, 0)

        is_stock_exceeded = stock.quantity - quantity_allocated < line_info.quantity
        if is_stock_exceeded and not allow_stock_to_be_exceeded:
            insufficient_stocks.append(
                InsufficientStockData(
                    variant=variant,  # type: ignore
                    order_line=line_info.line,
                    warehouse_pk=warehouse_pk,
                )
            )
            continue
        stock.quantity = stock.quantity - line_info.quantity
        stocks_to_update.append(stock)

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)

    Stock.objects.bulk_update(stocks_to_update, ["quantity"])


def get_order_lines_with_track_inventory(
    order_lines_info: Iterable["OrderLineInfo"],
) -> Iterable["OrderLineInfo"]:
    """Return order lines with variants with track inventory set to True."""
    return [
        line_info
        for line_info in order_lines_info
        if line_info.variant
        and line_info.variant.track_inventory
        and not line_info.variant.is_preorder_active()
    ]


@traced_atomic_transaction()
def deallocate_stock_for_order(order: "Order", manager: PluginsManager):
    """Remove all allocations for given order."""
    lines = OrderLine.objects.filter(order_id=order.id)
    allocations = Allocation.objects.filter(
        Exists(lines.filter(id=OuterRef("order_line_id"))), quantity_allocated__gt=0
    ).select_related("stock")

    stocks_to_update = []
    for alloc in allocations:
        stock = alloc.stock
        stock.quantity_allocated = F("quantity_allocated") - alloc.quantity_allocated
        stocks_to_update.append(stock)

    for allocation in allocations.annotate_stock_available_quantity():
        if allocation.stock_available_quantity <= 0:
            transaction.on_commit(
                lambda: manager.product_variant_back_in_stock(allocation.stock)
            )

    allocations.update(quantity_allocated=0)
    Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])


@traced_atomic_transaction()
def allocate_preorders(
    order_lines_info: Iterable["OrderLineInfo"],
    channel_slug: str,
    check_reservations: bool = False,
    checkout_lines: Optional[Iterable["CheckoutLine"]] = None,
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
    quantity_allocation_for_channel: Dict = defaultdict(int)
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
        )  # type: ignore
        listings_reservations: Dict = defaultdict(int)
        for reservation in quantity_reservation_list:
            listings_reservations[
                reservation["product_variant_channel_listing"]
            ] += reservation["quantity_reserved_sum"]
    else:
        listings_reservations = defaultdict(int)

    variants_global_allocations: Dict[int, int] = defaultdict(int)
    for channel_listing in all_variants_channel_listings:
        variants_global_allocations[
            channel_listing["variant_id"]
        ] += quantity_allocation_for_channel[channel_listing["id"]]

    insufficient_stocks: List[InsufficientStockData] = []
    allocations: List[PreorderAllocation] = []
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
    order_lines_info: Iterable["OrderLineInfo"],
) -> Iterable["OrderLineInfo"]:
    """Return order lines with variants with preorder flag set to True."""
    return [
        line_info
        for line_info in order_lines_info
        if line_info.variant and line_info.variant.is_preorder_active()
    ]


def _create_preorder_allocation(
    line_info: "OrderLineInfo",
    variant_channel_data: Tuple[int, Optional[int]],
    variant_global_allocation: int,
    variants_channel_listings: List[int],
    quantity_allocation_for_channel: Dict[int, int],
    listings_reservations: Dict[int, int],
) -> Tuple[Optional[PreorderAllocation], Optional[InsufficientStockData]]:
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
    preorder_allocations = PreorderAllocation.objects.filter(
        product_variant_channel_listing_id__in=channel_listings_pk
    ).select_related("order_line", "order_line__order")

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
            shipping_zones__id=order.shipping_method.shipping_zone_id  # type: ignore
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
        (
            Stock.objects.select_for_update(of=("self",)).filter(
                warehouse=warehouse, product_variant=product_variant
            )
        )
    )

    return (stock[0] if stock else None) or Stock(
        warehouse=warehouse, product_variant=product_variant, quantity=0
    )
