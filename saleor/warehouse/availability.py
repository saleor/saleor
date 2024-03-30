from collections import defaultdict
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    NoReturn,
    Optional,
)

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet, Sum
from django.db.models.functions import Coalesce

from ..checkout.error_codes import CheckoutErrorCode
from ..checkout.fetch import DeliveryMethodBase
from ..core.exceptions import InsufficientStock, InsufficientStockData
from ..product.models import ProductVariantChannelListing
from .models import Reservation, Stock, StockQuerySet
from .reservations import get_listings_reservations

if TYPE_CHECKING:
    from ..checkout.fetch import CheckoutLineInfo
    from ..checkout.models import CheckoutLine
    from ..order.models import OrderLine
    from ..product.models import Product, ProductVariant


class ChannelListingPreorderAvailbilityInfo(NamedTuple):
    preorder_quantity: int
    preorder_quantity_threshold: int
    listing_id: int


class VariantsChannelAvailbilityInfo(NamedTuple):
    variants_channel_availability: dict[int, ChannelListingPreorderAvailbilityInfo]
    variants_global_allocations: dict[int, int]
    all_variants_channel_listings: QuerySet[ProductVariantChannelListing]
    variant_channels: dict[int, list[ProductVariantChannelListing]]


def _get_available_quantity(
    stocks: StockQuerySet,
    checkout_lines: Optional[list["CheckoutLine"]] = None,
    check_reservations: bool = False,
) -> int:
    results = stocks.aggregate(
        total_quantity=Coalesce(Sum("quantity", distinct=True), 0),
        quantity_allocated=Coalesce(Sum("allocations__quantity_allocated"), 0),
    )
    total_quantity = results["total_quantity"]
    quantity_allocated = results["quantity_allocated"]

    if check_reservations:
        quantity_reserved = get_reserved_stock_quantity(stocks, checkout_lines)
    else:
        quantity_reserved = 0

    return max(total_quantity - quantity_allocated - quantity_reserved, 0)


def check_stock_and_preorder_quantity(
    variant: "ProductVariant",
    country_code: str,
    channel_slug: str,
    quantity: int,
    checkout_lines: Optional[list["CheckoutLine"]] = None,
    check_reservations: bool = False,
    order_line: Optional["OrderLine"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Validate if there is stock/preorder available for given variant.

    :raises InsufficientStock: when there is not enough items in stock for a variant
    or there is not enough available preorder items for a variant.
    """
    if variant.is_preorder_active():
        check_preorder_threshold_in_orders(
            variant,
            quantity,
            channel_slug,
            checkout_lines,
            check_reservations,
            database_connection_name=database_connection_name,
        )
    else:
        check_stock_quantity(
            variant,
            country_code,
            channel_slug,
            quantity,
            checkout_lines,
            check_reservations,
            order_line,
            database_connection_name,
        )


def check_stock_quantity(
    variant: "ProductVariant",
    country_code: str,
    channel_slug: str,
    quantity: int,
    checkout_lines: Optional[list["CheckoutLine"]] = None,
    check_reservations: bool = False,
    order_line: Optional["OrderLine"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Validate if there is stock available for given variant in given country.

    If so - returns None. If there is less stock then required raise InsufficientStock
    exception.
    """
    if variant.track_inventory:
        stocks = Stock.objects.using(
            database_connection_name
        ).get_variant_stocks_for_country(country_code, channel_slug, variant)
        if not stocks:
            raise InsufficientStock(
                [
                    InsufficientStockData(
                        variant=variant, available_quantity=0, order_line=order_line
                    )
                ]
            )

        available_quantity = _get_available_quantity(
            stocks, checkout_lines, check_reservations
        )
        if quantity > available_quantity:
            raise InsufficientStock(
                [
                    InsufficientStockData(
                        variant=variant, available_quantity=0, order_line=order_line
                    )
                ]
            )


def check_stock_and_preorder_quantity_bulk(
    variants: Iterable["ProductVariant"],
    country_code: str,
    quantities: Iterable[int],
    channel_slug: str,
    global_quantity_limit: Optional[int],
    delivery_method_info: Optional["DeliveryMethodBase"] = None,
    additional_filter_lookup: Optional[dict[str, Any]] = None,
    existing_lines: Optional[Iterable["CheckoutLineInfo"]] = None,
    replace: bool = False,
    check_reservations: bool = False,
):
    """Validate if products are available for stocks/preorder.

    :raises InsufficientStock: when there is not enough items in stock for a variant
    or there is not enough available preorder items for a variant.
    """
    (
        stock_variants,
        stock_quantities,
        preorder_variants,
        preorder_quantities,
    ) = _split_lines_for_trackable_and_preorder(variants, quantities)
    if stock_variants:
        check_stock_quantity_bulk(
            stock_variants,
            country_code,
            stock_quantities,
            channel_slug,
            global_quantity_limit,
            delivery_method_info,
            additional_filter_lookup,
            existing_lines,
            replace,
            check_reservations,
        )
    if preorder_variants:
        check_preorder_threshold_bulk(
            preorder_variants,
            preorder_quantities,
            channel_slug,
            global_quantity_limit,
            existing_lines,
            replace,
            check_reservations,
        )


def _split_lines_for_trackable_and_preorder(
    variants: Iterable["ProductVariant"], quantities: Iterable[int]
) -> tuple[
    Iterable["ProductVariant"], Iterable[int], Iterable["ProductVariant"], Iterable[int]
]:
    """Return variants and quantities splitted by "is_preorder_active"."""
    stock_variants, stock_quantities = [], []
    preorder_variants, preorder_quantities = [], []

    for variant, quantity in zip(variants, quantities):
        if variant.is_preorder_active():
            preorder_variants.append(variant)
            preorder_quantities.append(quantity)
        else:
            stock_variants.append(variant)
            stock_quantities.append(quantity)
    return (
        stock_variants,
        stock_quantities,
        preorder_variants,
        preorder_quantities,
    )


def _check_quantity_limits(
    variant: "ProductVariant", quantity: int, global_quantity_limit: Optional[int]
) -> Optional[NoReturn]:
    quantity_limit = variant.quantity_limit_per_customer or global_quantity_limit

    if quantity_limit is not None and quantity > quantity_limit:
        raise ValidationError(
            {
                "quantity": ValidationError(
                    (
                        f"Cannot add more than {quantity_limit} "
                        f"times this item: {variant}."
                    ),
                    code=CheckoutErrorCode.QUANTITY_GREATER_THAN_LIMIT.value,
                )
            }
        )
    return None


def check_stock_quantity_bulk(
    variants: Iterable["ProductVariant"],
    country_code: str,
    quantities: Iterable[int],
    channel_slug: str,
    global_quantity_limit: Optional[int],
    delivery_method_info: Optional["DeliveryMethodBase"] = None,
    additional_filter_lookup: Optional[dict[str, Any]] = None,
    existing_lines: Optional[Iterable["CheckoutLineInfo"]] = None,
    replace=False,
    check_reservations: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Validate if there is stock available for given variants in given country.

    :raises InsufficientStock: when there is not enough items in stock for a variant.
    """
    filter_lookup = {"product_variant__in": variants}
    if additional_filter_lookup is not None:
        filter_lookup.update(additional_filter_lookup)

    # in case when the delivery method is not set yet, we should check the stock
    # quantity in standard warehouses available in a given channel and country, and
    # in the collection point warehouses for the channel
    include_cc_warehouses = (
        not delivery_method_info.delivery_method if delivery_method_info else True
    )
    # in case of click and collect order, we need to check local or global stock
    # regardless of the country code
    collection_point = (
        delivery_method_info.warehouse_pk if delivery_method_info else None
    )
    stocks = (
        Stock.objects.using(database_connection_name).for_channel_and_click_and_collect(
            channel_slug
        )
        if collection_point
        else Stock.objects.using(database_connection_name).for_channel_and_country(
            channel_slug, country_code, include_cc_warehouses
        )
    )

    all_variants_stocks = stocks.filter(**filter_lookup).annotate_available_quantity()

    variant_stocks: dict[int, list[Stock]] = defaultdict(list)
    for stock in all_variants_stocks:
        variant_stocks[stock.product_variant_id].append(stock)

    if check_reservations:
        variant_reservations = get_reserved_stock_quantity_bulk(
            all_variants_stocks,
            [line.line for line in existing_lines] if existing_lines else [],
        )
    else:
        variant_reservations = defaultdict(int)

    insufficient_stocks: list[InsufficientStockData] = []
    variants_quantities = {
        line.variant.pk: line.line.quantity for line in existing_lines or []
    }
    for variant, quantity in zip(variants, quantities):
        if not replace:
            quantity += variants_quantities.get(variant.pk, 0)

        stocks = variant_stocks.get(variant.pk, [])
        available_quantity = sum([stock.available_quantity for stock in stocks])
        available_quantity = max(
            available_quantity - variant_reservations[variant.pk], 0
        )

        if quantity > 0:
            _check_quantity_limits(variant, quantity, global_quantity_limit)

            if not variant.track_inventory:
                continue

            if not stocks:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant=variant, available_quantity=available_quantity
                    )
                )
            elif quantity > available_quantity:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant=variant,
                        available_quantity=available_quantity,
                    )
                )

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)


def _get_variants_channel_availability_info(
    variants: Iterable["ProductVariant"],
    channel_slug: str,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> VariantsChannelAvailbilityInfo:
    all_variants_channel_listings = (
        ProductVariantChannelListing.objects.using(database_connection_name)
        .filter(variant__in=variants)
        .annotate_preorder_quantity_allocated()
        .annotate(
            available_preorder_quantity=F("preorder_quantity_threshold")
            - Coalesce(Sum("preorder_allocations__quantity"), 0),
        )
        .select_related("channel")
    )
    variants_channel_availability = {
        channel_listing.variant_id: ChannelListingPreorderAvailbilityInfo(
            channel_listing.available_preorder_quantity,
            channel_listing.preorder_quantity_threshold,
            channel_listing.id,
        )
        for channel_listing in all_variants_channel_listings
        if channel_listing.channel.slug == channel_slug
    }

    variant_channels: dict[int, list[ProductVariantChannelListing]] = defaultdict(list)
    for channel_listing in all_variants_channel_listings:
        variant_channels[channel_listing.variant_id].append(channel_listing)

    variants_global_allocations = {
        variant_id: sum(
            channel_listing.preorder_quantity_allocated  # type: ignore
            for channel_listing in channel_listings
        )
        for variant_id, channel_listings in variant_channels.items()
    }
    return VariantsChannelAvailbilityInfo(
        variants_channel_availability,
        variants_global_allocations,
        all_variants_channel_listings,
        variant_channels,
    )


def check_preorder_threshold_in_orders(
    variant: "ProductVariant",
    quantity: int,
    channel_slug: str,
    checkout_lines: Optional[Iterable["CheckoutLine"]],
    check_reservations: bool,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Validate if there is preorder available for given variants in given country.

    It is used in orders, since it does not need additional logic related to limits.
    :raises InsufficientStock: when there is not enough items in stock for a variant.
    """
    (
        variants_channel_availability,
        variants_global_allocations,
        all_variants_channel_listings,
        variant_channels,
    ) = _get_variants_channel_availability_info(
        [variant], channel_slug, database_connection_name=database_connection_name
    )

    if check_reservations:
        listings_reservations = get_listings_reservations(
            checkout_lines,
            all_variants_channel_listings,
            database_connection_name=database_connection_name,
        )
    else:
        listings_reservations = defaultdict(int)

    insufficient_stocks: list[InsufficientStockData] = []

    if (
        variants_channel_availability[variant.id].preorder_quantity_threshold
        is not None
    ):
        channel_listing_id = variants_channel_availability[variant.id].listing_id
        available_channel_quantity = variants_channel_availability[
            variant.id
        ].preorder_quantity
        available_channel_quantity -= listings_reservations[channel_listing_id]
        available_channel_quantity = max(available_channel_quantity, 0)

        if quantity > available_channel_quantity:
            insufficient_stocks.append(
                InsufficientStockData(
                    variant=variant, available_quantity=available_channel_quantity
                )
            )

        if variant.preorder_global_threshold is not None:
            global_availability = variant.preorder_global_threshold
            global_availability -= variants_global_allocations[variant.id]

            for channel_listing in variant_channels[variant.id]:
                global_availability -= listings_reservations[channel_listing.id]

            global_availability = max(global_availability, 0)

            if quantity > global_availability:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant=variant,
                        available_quantity=global_availability,
                    )
                )

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)


def check_preorder_threshold_bulk(
    variants: Iterable["ProductVariant"],
    quantities: Iterable[int],
    channel_slug: str,
    global_quantity_limit: Optional[int],
    existing_lines: Optional[Iterable["CheckoutLineInfo"]] = None,
    replace: bool = False,
    check_reservations: bool = False,
):
    """Validate if there is enough preordered variants according to thresholds.

    :raises InsufficientStock: when there is not enough available items for a variant.
    """
    (
        variants_channel_availability,
        variants_global_allocations,
        all_variants_channel_listings,
        variant_channels,
    ) = _get_variants_channel_availability_info(variants, channel_slug)

    if check_reservations:
        listings_reservations = get_listings_reservations(
            [line.line for line in existing_lines or []], all_variants_channel_listings
        )
    else:
        listings_reservations = defaultdict(int)

    insufficient_stocks: list[InsufficientStockData] = []
    variants_quantities = {
        line.variant.pk: line.line.quantity for line in existing_lines or []
    }
    for variant, quantity in zip(variants, quantities):
        cumulative_quantity = quantity
        if not replace:
            cumulative_quantity = quantity + variants_quantities.get(variant.pk, 0)

        if quantity > 0:
            _check_quantity_limits(variant, cumulative_quantity, global_quantity_limit)

        if (
            variants_channel_availability[variant.id].preorder_quantity_threshold
            is not None
        ):
            channel_listing_id = variants_channel_availability[variant.id].listing_id
            available_channel_quantity = variants_channel_availability[
                variant.id
            ].preorder_quantity
            available_channel_quantity -= listings_reservations[channel_listing_id]
            available_channel_quantity = max(available_channel_quantity, 0)
            if quantity > available_channel_quantity:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant=variant,
                        available_quantity=available_channel_quantity,
                    )
                )

        if variant.preorder_global_threshold is not None:
            global_availability = variant.preorder_global_threshold
            global_availability -= variants_global_allocations[variant.id]

            for channel_listing in variant_channels[variant.id]:
                global_availability -= listings_reservations[channel_listing.id]

            global_availability = max(global_availability, 0)

            if quantity > global_availability:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant=variant,
                        available_quantity=global_availability,
                    )
                )

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)


def get_available_quantity(
    variant: "ProductVariant",
    country_code: str,
    channel_slug: str,
    checkout_lines: Optional[list["CheckoutLine"]] = None,
    check_reservations: bool = False,
) -> int:
    """Return available quantity for given product in given country."""
    stocks = Stock.objects.get_variant_stocks_for_country(
        country_code, channel_slug, variant
    )
    if not stocks:
        return 0
    return _get_available_quantity(stocks, checkout_lines, check_reservations)


def is_product_in_stock(
    product: "Product", country_code: str, channel_slug: str
) -> bool:
    """Check if there is any variant of given product available in given country."""
    stocks = Stock.objects.get_product_stocks_for_country_and_channel(
        country_code, channel_slug, product
    ).annotate_available_quantity()
    return any(stocks.values_list("available_quantity", flat=True))


def get_reserved_stock_quantity(
    stocks: StockQuerySet, lines: Optional[list["CheckoutLine"]] = None
) -> int:
    result = (
        Reservation.objects.filter(
            stock__in=stocks,
        )
        .not_expired()
        .exclude_checkout_lines(lines)
        .aggregate(
            quantity_reserved=Coalesce(Sum("quantity_reserved"), 0),
        )
    )

    return result["quantity_reserved"]


def get_reserved_stock_quantity_bulk(
    stocks: Iterable[Stock],
    checkout_lines: Iterable["CheckoutLine"],
) -> dict[int, int]:
    reservations: dict[int, int] = defaultdict(int)
    if not stocks:
        return reservations

    result = (
        Reservation.objects.filter(
            stock__in=stocks,
        )
        .not_expired()
        .exclude_checkout_lines(checkout_lines)
        .values("stock_id")
        .annotate(
            quantity_reserved=Coalesce(Sum("quantity_reserved"), 0),
        )
    )

    stocks_variants = {stock.id: stock.product_variant_id for stock in stocks}
    for stock_reservations in result:
        variant_id = stocks_variants.get(stock_reservations["stock_id"])
        if variant_id:
            reservations[variant_id] += stock_reservations["quantity_reserved"]

    return reservations
