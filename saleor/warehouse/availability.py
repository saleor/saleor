from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db.models import Sum

from ..core.exceptions import InsufficientStock
from .models import Stock

if TYPE_CHECKING:
    from ..product.models import Product, ProductVariant


def check_stock_quantity(variant: "ProductVariant", country_code: str, quantity: int):
    """Validate if there is stock available for given variant in given country.

    If so - returns None. If there is less stock then required rise InsufficientStock
    exception.
    """
    try:
        stock = Stock.objects.get_variant_stock_for_country(country_code, variant)
    except Stock.DoesNotExist:
        raise InsufficientStock(variant)

    if variant.track_inventory and quantity > stock.quantity_available:
        raise InsufficientStock(variant)


def get_available_quantity(variant: "ProductVariant", country_code: str) -> int:
    """Return available quantity for given product in given country."""
    try:
        stock = Stock.objects.get_variant_stock_for_country(country_code, variant)
    except Stock.DoesNotExist:
        return 0
    return stock.quantity_available


def get_quantity_allocated(variant: "ProductVariant", country_code: str) -> int:
    try:
        stock = Stock.objects.get_variant_stock_for_country(country_code, variant)
    except Stock.DoesNotExist:
        return 0
    return stock.quantity_allocated


def is_variant_in_stock(variant: "ProductVariant", country_code: str) -> bool:
    """Check if variant is available in given country."""
    quantity_available = get_available_quantity(variant, country_code)
    return quantity_available > 0


def stocks_for_product(product: "Product", country_code: str):
    return (
        Stock.objects.annotate_available_quantity()
        .for_country(country_code)
        .filter(product_variant__product_id=product.pk)
    )


def is_product_in_stock(product: "Product", country_code: str) -> bool:
    """Check if there is any variant of given product available in given country."""
    return any(
        stocks_for_product(product, country_code).values_list(
            "available_quantity", flat=True
        )
    )


def are_all_product_variants_in_stock(product: "Product", country_code: str) -> bool:
    """Check if all variants of given product are available in given country."""
    product_stocks = (
        stocks_for_product(product, country_code)
        .values_list("available_quantity", "product_variant_id")
        .all()
    )
    are_all_available = all([elem[0] for elem in product_stocks])
    variants_with_stocks = [elem[1] for elem in product_stocks]

    product_variants = product.variants.exclude(id__in=variants_with_stocks).exists()
    return are_all_available and not product_variants


def products_with_low_stock(threshold: Optional[int] = None):
    """Return queryset with stock lower than given threshold."""
    if threshold is None:
        threshold = settings.LOW_STOCK_THRESHOLD
    stocks = (
        Stock.objects.select_related("product_variant")
        .values("product_variant__product_id", "warehouse_id")
        .annotate(total_stock=Sum("quantity"))
    )
    return stocks.filter(total_stock__lte=threshold).distinct()


def get_available_quantity_for_customer(stock: Stock) -> int:
    """Return maximum checkout line quantity."""
    return min(stock.quantity_available, settings.MAX_CHECKOUT_LINE_QUANTITY)
