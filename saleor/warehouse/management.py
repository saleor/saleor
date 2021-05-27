from collections import defaultdict, namedtuple
from typing import TYPE_CHECKING, Dict, Iterable, List, cast

from django.db.models import F, Sum

from ..core.exceptions import AllocationError, InsufficientStock, InsufficientStockData
from ..core.tracing import traced_atomic_transaction
from ..order import OrderLineData
from ..product.models import ProductVariant
from .models import Allocation, Stock, Warehouse

if TYPE_CHECKING:
    from ..order.models import Order, OrderLine


StockData = namedtuple("StockData", ["pk", "quantity"])


@traced_atomic_transaction()
def allocate_stocks(
    order_lines_info: Iterable["OrderLineData"], country_code: str, channel_slug: str
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

    variants = [line_info.variant for line_info in order_lines_info]

    stocks = list(
        Stock.objects.select_for_update(of=("self",))
        .for_country_and_channel(country_code, channel_slug)
        .filter(product_variant__in=variants)
        .order_by("pk")
        .values("id", "product_variant", "pk", "quantity")
    )
    stocks_id = (stock.pop("id") for stock in stocks)

    quantity_allocation_list = list(
        Allocation.objects.filter(
            stock_id__in=stocks_id,
            quantity_allocated__gt=0,
        )
        .values("stock")
        .annotate(quantity_allocated_sum=Sum("quantity_allocated"))
    )
    quantity_allocation_for_stocks: Dict = defaultdict(int)
    for allocation in quantity_allocation_list:
        quantity_allocation_for_stocks[allocation["stock"]] += allocation[
            "quantity_allocated_sum"
        ]

    variant_to_stocks: Dict[str, List[StockData]] = defaultdict(list)
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
            insufficient_stock,
        )
        allocations.extend(allocation_items)

    if insufficient_stock:
        raise InsufficientStock(insufficient_stock)

    if allocations:
        Allocation.objects.bulk_create(allocations)


def _create_allocations(
    line_info: "OrderLineData",
    stocks: List[StockData],
    quantity_allocation_for_stocks: dict,
    insufficient_stock: List[InsufficientStockData],
):
    quantity = line_info.quantity
    quantity_allocated = 0
    allocations = []
    for stock_data in stocks:
        quantity_allocated_in_stock = quantity_allocation_for_stocks.get(
            stock_data.pk, 0
        )

        quantity_available_in_stock = stock_data.quantity - quantity_allocated_in_stock

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


@traced_atomic_transaction()
def deallocate_stock(order_lines_data: Iterable["OrderLineData"]):
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

    line_to_allocations: Dict[int, List[Allocation]] = defaultdict(list)
    for allocation in lines_allocations:
        line_to_allocations[allocation.order_line_id].append(allocation)

    allocations_to_update = []
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
                quantity_dealocated += quantity_to_deallocate
                allocations_to_update.append(allocation)
                if quantity_dealocated == quantity:
                    break
        if not quantity_dealocated == quantity:
            not_dellocated_lines.append(order_line)

    if not_dellocated_lines:
        raise AllocationError(not_dellocated_lines)

    Allocation.objects.bulk_update(allocations_to_update, ["quantity_allocated"])


@traced_atomic_transaction()
def increase_stock(
    order_line: "OrderLine",
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


@traced_atomic_transaction()
def increase_allocations(lines_info: Iterable["OrderLineData"], channel_slug: str):
    """Increase allocation for order lines with appropriate quantity."""
    line_pks = [info.line.pk for info in lines_info]
    allocations = list(
        Allocation.objects.filter(order_line__in=line_pks)
        .select_related("stock", "order_line")
        .select_for_update(of=("self", "stock"))
    )
    # evaluate allocations query to trigger select_for_update lock
    allocation_pks_to_delete = [alloc.pk for alloc in allocations]
    allocation_quantity_map: Dict[int, list] = defaultdict(list)

    for alloc in allocations:
        allocation_quantity_map[alloc.order_line.pk].append(alloc.quantity_allocated)

    for line_info in lines_info:
        allocated = sum(allocation_quantity_map[line_info.line.pk])
        # line_info.quantity resembles amount to add, sum it with already allocated.
        line_info.quantity += allocated

    Allocation.objects.filter(pk__in=allocation_pks_to_delete).delete()

    allocate_stocks(
        lines_info,
        lines_info[0].line.order.shipping_address.country.code,  # type: ignore
        channel_slug,
    )


def decrease_allocations(lines_info: Iterable["OrderLineData"]):
    """Decreate allocations for provided order lines."""
    tracked_lines = get_order_lines_with_track_inventory(lines_info)
    if not tracked_lines:
        return
    decrease_stock(tracked_lines, update_stocks=False)


@traced_atomic_transaction()
def decrease_stock(order_lines_info: Iterable["OrderLineData"], update_stocks=True):
    """Decrease stocks quantities for given `order_lines` in given warehouses.

    Function deallocate as many quantities as requested if order_line has less quantity
    from requested function deallocate whole quantity. Next function try to find the
    stock in a given warehouse, if stock not exists or have not enough stock,
    the function raise InsufficientStock exception. When the stock has enough quantity
    function decrease it by given value.
    If update_stocks is False, allocations will decrease but stocks quantities
    will stay unmodified (case of unconfirmed order editing).
    """
    variants = [line_info.variant for line_info in order_lines_info]
    warehouse_pks = [line_info.warehouse_pk for line_info in order_lines_info]
    try:
        deallocate_stock(order_lines_info)
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

    quantity_allocation_for_stocks: Dict[int, int] = defaultdict(int)
    for allocation in quantity_allocation_list:
        quantity_allocation_for_stocks[allocation["stock"]] += allocation[
            "quantity_allocated__sum"
        ]

    if update_stocks:
        _decrease_stocks_quantity(
            order_lines_info,
            variant_and_warehouse_to_stock,
            quantity_allocation_for_stocks,
        )


def _decrease_stocks_quantity(
    order_lines_info: Iterable["OrderLineData"],
    variant_and_warehouse_to_stock: Dict[int, Dict[str, Stock]],
    quantity_allocation_for_stocks: Dict[int, int],
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
            insufficient_stocks.append(
                InsufficientStockData(
                    variant, line_info.line, warehouse_pk  # type: ignore
                )
            )
            continue

        quantity_allocated = quantity_allocation_for_stocks.get(stock.pk, 0)

        if stock.quantity - quantity_allocated < line_info.quantity:
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
    order_lines_info: Iterable["OrderLineData"],
) -> Iterable["OrderLineData"]:
    """Return order lines with variants with track inventory set to True."""
    return [
        line_info
        for line_info in order_lines_info
        if line_info.variant and line_info.variant.track_inventory
    ]


@traced_atomic_transaction()
def deallocate_stock_for_order(order: "Order"):
    """Remove all allocations for given order."""
    allocations = Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).select_for_update(of=("self",))
    allocations.update(quantity_allocated=0)
