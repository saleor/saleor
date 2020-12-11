from collections import defaultdict
from typing import TYPE_CHECKING, Iterable, List, Optional

from django.db.models import Sum
from django.db.models.functions import Coalesce

from ..core.exceptions import InsufficientStock, InsufficientStockData
from ..reservation.stock import (
    get_reserved_quantity,
    get_reserved_quantity_bulk,
)
from .models import Stock, StockQuerySet

if TYPE_CHECKING:
    from ..account.models import User
    from ..product.models import Product, ProductVariant


def _get_available_quantity(stocks: StockQuerySet) -> int:
    results = stocks.aggregate(
        total_quantity=Coalesce(Sum("quantity", distinct=True), 0),
        quantity_allocated=Coalesce(Sum("allocations__quantity_allocated"), 0),
    )
    total_quantity = results["total_quantity"]
    quantity_allocated = results["quantity_allocated"]

    return max(total_quantity - quantity_allocated, 0)


def check_stock_quantity(
    variant: "ProductVariant",
    country_code: str,
    quantity: int,
    user: Optional["User"] = None,
):
    """Validate if there is stock available for given variant in given country.

    If so - returns None. If there is less stock then required raise InsufficientStock
    exception.
    """
    if variant.track_inventory:
        stocks = Stock.objects.get_variant_stocks_for_country(country_code, variant)
        if not stocks:
            raise InsufficientStock([InsufficientStockData(variant=variant)])

        reserved_quantity = get_reserved_quantity(variant, country_code, user)
        available_quantity = max(_get_available_quantity(stocks) - reserved_quantity, 0)
        if quantity > available_quantity:
            raise InsufficientStock([InsufficientStockData(variant=variant)])


def check_stock_quantity_bulk(variants: Iterable["ProductVariant"], country_code: str, quantities: int, user: Optional["User"]=None):
    """Validate if there is stock available for given variants in given country.

    If user argument is specified, their reserved amounts are excluded.

    :raises InsufficientStock: when there is not enough items in stock for a variant.
    """
    all_variants_stocks = (
        Stock.objects.for_country(country_code)
        .filter(product_variant__in=variants)
        .annotate_available_quantity()
    )

    variant_stocks = defaultdict(list)
    for stock in all_variants_stocks:
        variant_stocks[stock.product_variant_id].append(stock)

    variants_reservations = get_reserved_quantity_bulk(variants, country_code, user)

    insufficient_stocks: List[InsufficientStockData] = []
    for variant, quantity in zip(variants, quantities):
        stocks = variant_stocks.get(variant.pk, [])
        reserved_quantity = variants_reservations.get(variant.pk, 0)
        available_quantity = (
            sum([stock.available_quantity for stock in stocks]) - reserved_quantity
        )
        available_quantity = max(available_quantity, 0)

        if not stocks:
            insufficient_stocks.append(
                InsufficientStockData(
                    variant=variant, available_quantity=available_quantity
                )
            )

        if variant.track_inventory:
            if quantity > available_quantity:
                insufficient_stocks.append(
                    InsufficientStockData(
                        variant=variant, available_quantity=available_quantity
                    )
                )

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)


def get_available_quantity(variant: "ProductVariant", country_code: str, user: Optional["User"] = None) -> int:
    """Return available quantity for given product in given country."""
    stocks = Stock.objects.get_variant_stocks_for_country(country_code, variant)
    if not stocks:
        return 0
    available_quantity = _get_available_quantity(stocks)
    available_quantity -= get_reserved_quantity(variant, country_code, user)
    return max(available_quantity, 0)


def is_product_in_stock(product: "Product", country_code: str) -> bool:
    """Check if there is any variant of given product available in given country."""
    stocks = Stock.objects.get_product_stocks_for_country(
        country_code, product
    ).annotate_available_quantity()
    return any(stocks.values_list("available_quantity", flat=True))
