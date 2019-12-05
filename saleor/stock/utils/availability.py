from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db.models import Sum

from ...core.exceptions import InsufficientStock
from ...product.models import Product
from ..models import Stock

if TYPE_CHECKING:
    from ...product.models import ProductVariant


def check_stock_quantity(variant: "ProductVariant", country_code: str, quantity: int):
    try:
        stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    except Stock.DoesNotExist:
        raise InsufficientStock(variant)

    if variant.track_inventory and quantity > stock.quantity_available:
        raise InsufficientStock(variant)


def get_available_quantity(variant: "ProductVariant", country_code: str) -> int:
    try:
        stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    except Stock.DoesNotExist:
        return 0
    return stock.quantity_available


def is_variant_in_stock(variant: "ProductVariant", country_code: str) -> bool:
    stock = Stock.objects.for_country(country_code).get(product_variant__pk=variant.pk)
    return stock.is_available


def stocks_for_product(product: "Product", country_code: str):
    return (
        Stock.objects.annotate_available_quantity()
        .for_country(country_code)
        .filter(product_variant__product_id=product.pk)
    )


def is_product_in_stock(product: "Product", country_code: str) -> bool:
    return any(
        stocks_for_product(product, country_code).values_list(
            "available_quantity", flat=True
        )
    )


def are_all_product_variants_in_stock(product: "Product", country_code: str) -> bool:
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
    if threshold is None:
        threshold = getattr(settings, "LOW_STOCK_THRESHOLD", 3000)
    stocks = (
        Stock.objects.select_related("product_variant")
        .values("product_variant__product_id", "warehouse_id")
        .annotate(total_stock=Sum("quantity"))
    )
    return stocks.filter(total_stock__lte=threshold).distinct()
