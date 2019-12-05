from typing import TYPE_CHECKING

from .models import Stock

if TYPE_CHECKING:
    from ..product.models import ProductVariant


def allocate_stock(
    variant: "ProductVariant", country_code: str, quantity: int, commit: bool = True
) -> Stock:
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.allocate_stock(quantity, commit=commit)
    return stock


def deallocate_stock(
    variant: "ProductVariant", country_code: str, quantity: int, commit: bool = True
) -> Stock:
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.deallocate_stock(quantity, commit=commit)
    return stock


def increase_stock(
    variant: "ProductVariant",
    country_code: str,
    quantity: int,
    allocate: bool = False,
    commit: bool = True,
) -> Stock:
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.increase_stock(quantity, allocate=allocate, commit=commit)
    return stock


def decrease_stock(
    variant: "ProductVariant", country_code: str, quantity: int, commit: bool = True
) -> Stock:
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.decrease_stock(quantity, commit=commit)
    return stock
