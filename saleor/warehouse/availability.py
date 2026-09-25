from collections import defaultdict
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    NoReturn,
    Optional,
)

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db.models.functions import Coalesce

from ..checkout.error_codes import CheckoutErrorCode
from ..checkout.fetch import DeliveryMethodBase
from ..core.exceptions import InsufficientStock, InsufficientStockData
from .models import Reservation, Stock, StockQuerySet

if TYPE_CHECKING:
    from ..checkout.fetch import CheckoutLineInfo
    from ..checkout.models import CheckoutLine
    from ..order.models import OrderLine
    from ..product.models import Product, ProductVariant


def _get_available_quantity(
    stocks: StockQuerySet,
    checkout_lines: list["CheckoutLine"] | None = None,
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


def check_stock_quantity(
    variant: "ProductVariant",
    country_code: str,
    channel_slug: str,
    quantity: int,
    *,
    include_shipping_zones: bool,
    checkout_lines: list["CheckoutLine"] | None = None,
    check_reservations: bool = False,
    order_line: Optional["OrderLine"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Validate if there is stock available for given variant in given channel.

    If so - returns None. If there is less stock then required raise InsufficientStock
    exception.
    """
    if variant.track_inventory:
        stocks = Stock.objects.using(database_connection_name).get_variant_stocks(
            channel_slug,
            variant,
            country_code=country_code,
            include_shipping_zones=include_shipping_zones,
        )
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


def _check_quantity_limits(
    variant: "ProductVariant", quantity: int, global_quantity_limit: int | None
) -> NoReturn | None:
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
    global_quantity_limit: int | None,
    *,
    include_shipping_zones: bool,
    delivery_method_info: Optional["DeliveryMethodBase"] = None,
    additional_filter_lookup: dict[str, Any] | None = None,
    existing_lines: list["CheckoutLineInfo"] | None = None,
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

    if include_shipping_zones:
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
            Stock.objects.using(
                database_connection_name
            ).for_channel_and_click_and_collect(channel_slug)
            if collection_point
            else Stock.objects.using(database_connection_name).for_channel_or_country(
                channel_slug,
                country_code,
                include_shipping_zones=True,
                include_cc_warehouses=include_cc_warehouses,
            )
        )
    else:
        stocks = Stock.objects.using(database_connection_name).for_channel_or_country(
            channel_slug,
            include_shipping_zones=include_shipping_zones,
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
    for variant, quantity in zip(variants, quantities, strict=False):
        if not replace:
            quantity += variants_quantities.get(variant.pk, 0)

        stocks = variant_stocks.get(variant.pk, [])
        available_quantity = sum([stock.available_quantity for stock in stocks])  # type: ignore[attr-defined]
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


def get_available_quantity(
    variant: "ProductVariant",
    country_code: str,
    channel_slug: str,
    *,
    calculate_stocks_with_shipping_zones: bool,
    checkout_lines: list["CheckoutLine"] | None = None,
    check_reservations: bool = False,
) -> int:
    """Return available quantity for given product in given channel."""
    stocks = Stock.objects.get_variant_stocks(
        channel_slug,
        variant,
        country_code=country_code,
        include_shipping_zones=calculate_stocks_with_shipping_zones,
    )
    if not stocks:
        return 0
    return _get_available_quantity(stocks, checkout_lines, check_reservations)


def is_product_in_stock(
    product: "Product",
    country_code: str,
    channel_slug: str,
    calculate_stocks_with_shipping_zones: bool,
) -> bool:
    """Check if there is any variant of given product available in given channel."""
    stocks = Stock.objects.get_product_stocks(
        channel_slug,
        product,
        country_code=country_code,
        include_shipping_zones=calculate_stocks_with_shipping_zones,
    ).annotate_available_quantity()
    return any(stocks.values_list("available_quantity", flat=True))


def get_reserved_stock_quantity(
    stocks: StockQuerySet, lines: list["CheckoutLine"] | None = None
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
