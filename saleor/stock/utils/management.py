from typing import TYPE_CHECKING

from ..models import Stock

if TYPE_CHECKING:
    from ..product.models import ProductVariant


def allocate_stock(variant: "ProductVariant", country_code: str, quantity: int):
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.allocate_stock(quantity)


def deallocate_stock(variant: "ProductVariant", country_code: str, quantity: int):
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.deallocate_stock(quantity)


def increase_stock(variant: "ProductVariant", country_code: str, quantity: int):
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.increase_stock(quantity)


def decrease_stock(variant: "ProductVariant", country_code: str, quantity: int):
    stock = Stock.objects.for_country(country_code).get(product_variant=variant)
    stock.decrease_stock(quantity)
