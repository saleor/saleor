from typing import TYPE_CHECKING

from ...core.exceptions import InsufficientStock
from ..models import Stock

if TYPE_CHECKING:
    from ...product.models import Product, ProductVariant


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
    stocks = Stock.objects.for_country(country_code).filter(
        product_variant__pk=variant.pk
    )
    return stocks.exists()


def is_product_in_stock(product: "Product", country_code: str) -> bool:
    stocks = (
        Stock.objects.select_related("product_variant__product")
        .for_country(country_code)
        .filter(product_variant__product=product)
    )
    return stocks.exists()
