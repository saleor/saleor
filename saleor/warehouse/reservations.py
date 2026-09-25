import datetime
from collections import defaultdict
from collections.abc import Iterable
from typing import TYPE_CHECKING, NamedTuple

from django.db.models import Sum
from django.utils import timezone

from ..core.exceptions import InsufficientStock, InsufficientStockData
from ..core.tracing import traced_atomic_transaction
from ..product.models import ProductVariant
from .lock_objects import stock_qs_select_for_update
from .management import sort_stocks
from .models import Allocation, Reservation

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutLine


class StockData(NamedTuple):
    pk: int
    quantity: int


@traced_atomic_transaction()
def reserve_stocks_for_checkout(
    checkout_lines: Iterable["CheckoutLine"],
    lines_to_update_reservation_time: Iterable["CheckoutLine"],
    variants: Iterable["ProductVariant"],
    country_code: str,
    channel: "Channel",
    length_in_minutes: int,
    *,
    calculate_stocks_with_shipping_zones: bool,
    replace: bool = True,
):
    reserved_until = timezone.now() + datetime.timedelta(minutes=length_in_minutes)

    reserve_stocks(
        checkout_lines,
        variants,
        country_code,
        channel,
        reserved_until,
        replace=replace,
        calculate_stocks_with_shipping_zones=calculate_stocks_with_shipping_zones,
    )

    # Refresh reserved_until for already existing lines
    if lines_to_update_reservation_time:
        Reservation.objects.filter(
            checkout_line__in=lines_to_update_reservation_time
        ).update(reserved_until=reserved_until)


def reserve_stocks(
    checkout_lines: Iterable["CheckoutLine"],
    variants: Iterable["ProductVariant"],
    country_code: str,
    channel: "Channel",
    reserved_until: datetime.datetime,
    *,
    replace: bool = True,
    calculate_stocks_with_shipping_zones: bool,
):
    """Reserve stocks for given `checkout_lines` in given country."""
    variants_ids = [line.variant_id for line in checkout_lines]
    variants = [variant for variant in variants if variant.pk in variants_ids]
    variants_map = {variant.id: variant for variant in variants}

    # Reservation is only applied to checkout lines with variants with track inventory
    # set to True
    checkout_lines = get_checkout_lines_to_reserve(checkout_lines, variants_map)
    if not checkout_lines:
        return

    stocks = list(
        stock_qs_select_for_update()
        .get_variants_stocks(
            channel.slug,
            variants,
            country_code=country_code,
            include_shipping_zones=calculate_stocks_with_shipping_zones,
        )
        .order_by("pk")
        .values("id", "product_variant", "pk", "quantity", "warehouse_id")
    )
    stocks_id = [stock.pop("id") for stock in stocks]

    quantity_allocation_list = list(
        Allocation.objects.filter(
            stock_id__in=stocks_id,
            quantity_allocated__gt=0,
        )
        .values("stock")
        .annotate(quantity_allocated_sum=Sum("quantity_allocated"))
    )
    quantity_allocation_for_stocks: dict = defaultdict(int)
    for allocation in quantity_allocation_list:
        quantity_allocation_for_stocks[allocation["stock"]] += allocation[
            "quantity_allocated_sum"
        ]

    quantity_reservation_list = list(
        Reservation.objects.filter(
            stock_id__in=stocks_id,
            quantity_reserved__gt=0,
        )
        .not_expired()
        .exclude_checkout_lines(checkout_lines)
        .values("stock")
        .annotate(quantity_reserved_sum=Sum("quantity_reserved"))
    )
    quantity_reservation_for_stocks: dict = defaultdict(int)
    for reservation in quantity_reservation_list:
        quantity_reservation_for_stocks[reservation["stock"]] += reservation[
            "quantity_reserved_sum"
        ]

    stocks = sort_stocks(
        channel.allocation_strategy,
        stocks,
        channel,
        quantity_allocation_for_stocks,
    )

    variant_to_stocks: dict[int, list[StockData]] = defaultdict(list)
    for stock_data in stocks:
        variant = stock_data.pop("product_variant")
        variant_to_stocks[variant].append(StockData(**stock_data))

    insufficient_stocks: list[InsufficientStockData] = []
    reservations: list[Reservation] = []
    for line in checkout_lines:
        stock_reservations = variant_to_stocks[line.variant_id]
        insufficient_stocks, reserved_items = _create_stock_reservations(
            line,
            variants_map[line.variant_id],
            stock_reservations,
            quantity_allocation_for_stocks,
            quantity_reservation_for_stocks,
            insufficient_stocks,
            reserved_until,
        )
        reservations.extend(reserved_items)

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)

    if reservations:
        if replace:
            Reservation.objects.filter(checkout_line__in=checkout_lines).delete()
        Reservation.objects.bulk_create(reservations)


def _create_stock_reservations(
    line: "CheckoutLine",
    variant: "ProductVariant",
    stocks: list[StockData],
    quantity_allocation_for_stocks: dict,
    quantity_reservation_for_stocks: dict,
    insufficient_stocks: list[InsufficientStockData],
    reserved_until: datetime.datetime,
) -> tuple[list[InsufficientStockData], list[Reservation]]:
    quantity = line.quantity
    quantity_reserved = 0
    reservations = []
    for stock_data in stocks:
        quantity_allocated_in_stock = quantity_allocation_for_stocks.get(
            stock_data.pk, 0
        )
        quantity_reserved_in_stock = quantity_reservation_for_stocks.get(
            stock_data.pk, 0
        )

        quantity_available_in_stock = max(
            stock_data.quantity
            - quantity_allocated_in_stock
            - quantity_reserved_in_stock,
            0,
        )

        quantity_to_reserve = min(
            (quantity - quantity_reserved), quantity_available_in_stock
        )
        if quantity_to_reserve > 0:
            reservations.append(
                Reservation(
                    checkout_line=line,
                    stock_id=stock_data.pk,
                    quantity_reserved=quantity_to_reserve,
                    reserved_until=reserved_until,
                )
            )

            quantity_reserved += quantity_to_reserve
            if quantity_reserved == quantity:
                return insufficient_stocks, reservations

    if quantity_reserved != quantity:
        insufficient_stocks.append(
            InsufficientStockData(
                variant=variant,
                available_quantity=quantity,
            )
        )
        return insufficient_stocks, []

    return [], []


def get_checkout_lines_to_reserve(
    lines: Iterable["CheckoutLine"],
    variants_map: dict[int, "ProductVariant"],
) -> Iterable["CheckoutLine"]:
    """Return checkout lines which can be reserved."""
    valid_lines = []
    for line in lines:
        if (
            line.quantity
            and line.variant_id
            and variants_map[line.variant_id].track_inventory
        ):
            valid_lines.append(line)
    return valid_lines


def is_reservation_enabled(settings) -> bool:
    return bool(
        settings.reserve_stock_duration_authenticated_user
        or settings.reserve_stock_duration_anonymous_user
    )


def get_reservation_length(site, user) -> int | None:
    if user:
        return site.settings.reserve_stock_duration_authenticated_user
    return site.settings.reserve_stock_duration_anonymous_user
