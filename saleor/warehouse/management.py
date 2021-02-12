from collections import defaultdict, namedtuple
from typing import TYPE_CHECKING, Dict, Iterable, List, Tuple

from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from ..core.exceptions import AllocationError, InsufficientStock
from .models import Allocation, Stock, Warehouse

if TYPE_CHECKING:
    from ..order import OrderLineData
    from ..order.models import Order, OrderLine
    from ..product.models import ProductVariant


StockData = namedtuple("StockData", ["pk", "quantity"])


@transaction.atomic
def allocate_stocks(order_lines_info: Iterable["OrderLineData"], country_code: str):
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
    order_lines_info = [
        line_info
        for line_info in order_lines_info
        if line_info.variant and line_info.variant.track_inventory
    ]
    variants = [line_info.variant for line_info in order_lines_info]

    stocks = (
        Stock.objects.select_for_update(of=("self",))
        .for_country(country_code)
        .filter(product_variant__in=variants)
        .order_by("pk")
    )

    quantity_allocation_list = list(
        Allocation.objects.filter(
            stock__in=stocks,
            quantity_allocated__gt=0,
        )
        .values("stock")
        .annotate(Sum("quantity_allocated"))
    )
    quantity_allocation_for_stocks: Dict = defaultdict(int)
    for allocation in quantity_allocation_list:
        quantity_allocation_for_stocks[allocation["stock"]] += allocation[
            "quantity_allocated__sum"
        ]

    variant_to_stocks: Dict[str, List[StockData]] = defaultdict(list)
    for stock_data in stocks.values("product_variant", "pk", "quantity"):
        variant = stock_data.pop("product_variant")
        variant_to_stocks[variant].append(StockData(**stock_data))

    insufficient_stock: List["ProductVariant"] = []
    allocations: List[Allocation] = []
    for line_info in order_lines_info:
        stocks = variant_to_stocks[line_info.variant.pk]  # type: ignore
        insufficient_stock, allocation_items = _create_allocations(
            line_info, stocks, quantity_allocation_for_stocks, insufficient_stock
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
    insufficient_stock: List["ProductVariant"],
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
        insufficient_stock.append(line_info.variant)  # type: ignore
        return insufficient_stock, []


@transaction.atomic
def deallocate_stock(order_lines_with_quantities: List[Tuple["OrderLine", int]]):
    """Deallocate stocks for given `order_lines`.

    Function lock for update stocks and allocations related to given `order_lines`.
    Iterate over allocations sorted by `stock.pk` and deallocate as many items
    as needed of available in stock for order line, until deallocated all required
    quantity for the order line. If there is less quantity in stocks then
    raise an exception.
    """
    lines = [line for line, _ in order_lines_with_quantities]
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
    for order_line, quantity in order_lines_with_quantities:
        quantity_dealocated = 0
        allocations = line_to_allocations[order_line.pk]
        for allocation in allocations:
            quantity_to_deallocate = min(
                (quantity - quantity_dealocated), allocation.quantity_allocated
            )
            if quantity_to_deallocate > 0:
                allocation.quantity_allocated = (
                    F("quantity_allocated") - quantity_to_deallocate
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


@transaction.atomic
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


@transaction.atomic
def decrease_stock(order_line: "OrderLine", quantity: int, warehouse_pk: str):
    """Decrease stock quantity for given `order_line` in given warehouse.

    Function deallocate as many quantities as requested if order_line has less quantity
    from requested function deallocate whole quantity. Next function try to find the
    stock in a given warehouse, if stock not exists or have not enough stock,
    the function raise InsufficientStock exception. When the stock has enough quantity
    function decrease it by given value.
    """
    try:
        deallocate_stock([(order_line, quantity)])
    except AllocationError:
        order_line.allocations.update(quantity_allocated=0)

    try:
        stock = (
            order_line.variant.stocks.select_for_update()  # type: ignore
            .prefetch_related("allocations")
            .get(warehouse__pk=warehouse_pk)
        )
    except Stock.DoesNotExist:
        error_context = {"order_line": order_line, "warehouse_pk": warehouse_pk}
        raise InsufficientStock([order_line.variant], error_context)

    quantity_allocated = stock.allocations.aggregate(
        quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
    )["quantity_allocated"]

    if stock.quantity - quantity_allocated < quantity:
        error_context = {"order_line": order_line, "warehouse_pk": warehouse_pk}
        raise InsufficientStock([order_line.variant], error_context)

    stock.quantity = F("quantity") - quantity
    stock.save(update_fields=["quantity"])


@transaction.atomic
def deallocate_stock_for_order(order: "Order"):
    """Remove all allocations for given order."""
    allocations = Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).select_for_update(of=("self",))
    allocations.update(quantity_allocated=0)
