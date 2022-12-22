from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from ..core.exceptions import InsufficientStock, InsufficientStockData
from ..core.tracing import traced_atomic_transaction
from ..product.models import ProductVariant, ProductVariantChannelListing
from .management import sort_stocks
from .models import Allocation, PreorderReservation, Reservation, Stock

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutLine

StockData = namedtuple("StockData", ["pk", "quantity"])


@traced_atomic_transaction()
def reserve_stocks_and_preorders(
    checkout_lines: Iterable["CheckoutLine"],
    lines_to_update_reservation_time: Iterable["CheckoutLine"],
    variants: Iterable["ProductVariant"],
    country_code: str,
    channel: "Channel",
    length_in_minutes: int,
    *,
    replace: bool = True,
):
    stock_variants, stock_lines = [], []
    preorder_variants, preorder_lines = [], []

    for variant in variants:
        if variant.is_preorder_active():
            preorder_variants.append(variant)
        else:
            stock_variants.append(variant)

    for line in checkout_lines:
        if line.variant.is_preorder_active():
            preorder_lines.append(line)
        else:
            stock_lines.append(line)

    reserved_until = timezone.now() + timedelta(minutes=length_in_minutes)

    if stock_lines:
        reserve_stocks(
            stock_lines,
            stock_variants,
            country_code,
            channel,
            reserved_until,
            replace=replace,
        )

        # Refresh reserved_until for already existing lines
        if lines_to_update_reservation_time:
            Reservation.objects.filter(
                checkout_line__in=lines_to_update_reservation_time
            ).update(reserved_until=reserved_until)

    if preorder_lines:
        reserve_preorders(
            preorder_lines,
            preorder_variants,
            country_code,
            channel.slug,
            reserved_until,
            replace=replace,
        )

        # Refresh reserved_until for already existing lines
        if lines_to_update_reservation_time:
            PreorderReservation.objects.filter(
                checkout_line__in=lines_to_update_reservation_time
            ).update(reserved_until=reserved_until)


def reserve_stocks(
    checkout_lines: Iterable["CheckoutLine"],
    variants: Iterable["ProductVariant"],
    country_code: str,
    channel: "Channel",
    reserved_until: datetime,
    *,
    replace: bool = True,
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
        Stock.objects.select_for_update(of=("self",))
        .get_variants_stocks_for_country(country_code, channel.slug, variants)
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
    quantity_allocation_for_stocks: Dict = defaultdict(int)
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
    quantity_reservation_for_stocks: Dict = defaultdict(int)
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

    variant_to_stocks: Dict[int, List[StockData]] = defaultdict(list)
    for stock_data in stocks:
        variant = stock_data.pop("product_variant")
        variant_to_stocks[variant].append(StockData(**stock_data))

    insufficient_stocks: List[InsufficientStockData] = []
    reservations: List[Reservation] = []
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
    stocks: List[StockData],
    quantity_allocation_for_stocks: dict,
    quantity_reservation_for_stocks: dict,
    insufficient_stocks: List[InsufficientStockData],
    reserved_until: datetime,
) -> Tuple[List[InsufficientStockData], List[Reservation]]:
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


def reserve_preorders(
    checkout_lines: Iterable["CheckoutLine"],
    variants: Iterable["ProductVariant"],
    country_code: str,
    channel_slug: str,
    reserved_until: datetime,
    *,
    replace: bool = True,
):
    """Reserve preorders for given `checkout_lines` in given country."""
    variants_ids = [line.variant_id for line in checkout_lines]
    variants = [variant for variant in variants if variant.pk in variants_ids]
    variants_map = {variant.id: variant for variant in variants}

    all_variants_channel_listings = (
        ProductVariantChannelListing.objects.filter(variant__in=variants)
        .annotate_preorder_quantity_allocated()
        .annotate(
            available_preorder_quantity=F("preorder_quantity_threshold")
            - Coalesce(Sum("preorder_allocations__quantity"), 0),
        )
        .select_related("channel")
    )
    variants_channel_listings = {
        channel_listing.variant_id: channel_listing
        for channel_listing in all_variants_channel_listings
        if channel_listing.channel.slug == channel_slug
    }

    checkout_lines_to_reserve = []
    for line in checkout_lines:
        line_variant_channel_listing = variants_channel_listings[line.variant_id]
        if (
            line.variant.preorder_global_threshold
            or line_variant_channel_listing.preorder_quantity_threshold is not None
        ):
            checkout_lines_to_reserve.append(line)

    if not checkout_lines_to_reserve:
        return

    variant_channels: Dict[int, List[ProductVariantChannelListing]] = defaultdict(list)
    for channel_listing in all_variants_channel_listings:
        variant_channels[channel_listing.variant_id].append(channel_listing)

    variants_global_allocations = {
        variant_id: sum(
            channel_listing.preorder_quantity_allocated  # type: ignore
            for channel_listing in channel_listings
        )
        for variant_id, channel_listings in variant_channels.items()
    }

    listings_reservations: Dict = get_listings_reservations(
        checkout_lines, all_variants_channel_listings
    )

    insufficient_stocks: List[InsufficientStockData] = []
    reservations: List[PreorderReservation] = []
    for line in checkout_lines_to_reserve:
        insufficient_stocks, reservation = _create_preorder_reservation(
            line,
            variants_map[line.variant_id],
            variants_channel_listings[line.variant_id],
            variant_channels[line.variant_id],
            variants_global_allocations[line.variant_id],
            listings_reservations,
            insufficient_stocks,
            reserved_until,
        )
        if reservation:
            reservations.append(reservation)

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)

    if reservation:
        if replace:
            PreorderReservation.objects.filter(
                checkout_line__in=checkout_lines_to_reserve
            ).delete()
        PreorderReservation.objects.bulk_create(reservations)


def _create_preorder_reservation(
    line: "CheckoutLine",
    variant: "ProductVariant",
    listing: "ProductVariantChannelListing",
    all_listings: List["ProductVariantChannelListing"],
    global_allocations: int,
    listings_reservations: Dict[int, int],
    insufficient_stocks: List[InsufficientStockData],
    reserved_until: datetime,
):
    if listing.preorder_quantity_threshold is not None:
        available_channel_quantity = listing.available_preorder_quantity  # type: ignore
        available_channel_quantity = max(
            available_channel_quantity - listings_reservations[listing.id], 0
        )
        if line.quantity > available_channel_quantity:
            insufficient_stocks.append(
                InsufficientStockData(
                    variant=variant,
                    available_quantity=available_channel_quantity,
                )
            )

    if variant.preorder_global_threshold:
        # check global reservations
        available_global_quantity = variant.preorder_global_threshold
        available_global_quantity -= global_allocations
        global_reservations = 0
        for channel_listing in all_listings:
            global_reservations += listings_reservations[channel_listing.id]

        available_global_quantity -= global_reservations
        available_global_quantity = max(available_global_quantity, 0)

        if line.quantity > available_global_quantity:
            insufficient_stocks.append(
                InsufficientStockData(
                    variant=variant,
                    available_quantity=available_global_quantity,
                )
            )

    if listing.preorder_quantity_threshold or variant.preorder_global_threshold:
        # create reservation
        return insufficient_stocks, PreorderReservation(
            checkout_line=line,
            product_variant_channel_listing=listing,
            quantity_reserved=line.quantity,
            reserved_until=reserved_until,
        )

    return insufficient_stocks, None


def get_checkout_lines_to_reserve(
    lines: Iterable["CheckoutLine"],
    variants_map: Dict[int, "ProductVariant"],
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


def get_reservation_length(site, user) -> Optional[int]:
    if user:
        return site.settings.reserve_stock_duration_authenticated_user
    return site.settings.reserve_stock_duration_anonymous_user


def get_listings_reservations(
    checkout_lines: Optional[Iterable["CheckoutLine"]],
    all_variants_channel_listings,
) -> Dict[int, int]:
    quantity_reservation_list = (
        PreorderReservation.objects.filter(
            product_variant_channel_listing__in=all_variants_channel_listings,
            quantity_reserved__gt=0,
        )
        .not_expired()
        .exclude_checkout_lines(checkout_lines)
        .values("product_variant_channel_listing")
        .annotate(quantity_reserved_sum=Sum("quantity_reserved"))
    )
    listings_reservations: Dict = defaultdict(int)

    for reservation in quantity_reservation_list:
        listings_reservations[
            reservation["product_variant_channel_listing"]
        ] += reservation["quantity_reserved_sum"]

    return listings_reservations
