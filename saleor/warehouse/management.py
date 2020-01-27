from typing import TYPE_CHECKING

from django.db import transaction

from .models import Stock

if TYPE_CHECKING:
    from ..product.models import ProductVariant


@transaction.atomic
def allocate_stock(
    variant: "ProductVariant", country_code: str, quantity: int, commit: bool = True
) -> Stock:
    stock = Stock.objects.select_for_update(of=("self",)).get_variant_stock_for_country(
        country_code, variant
    )
    stock.allocate_stock(quantity, commit=commit)
    return stock


@transaction.atomic
def deallocate_stock(
    variant: "ProductVariant", country_code: str, quantity: int, commit: bool = True
) -> Stock:
    stock = Stock.objects.select_for_update(of=("self",)).get_variant_stock_for_country(
        country_code, variant
    )
    stock.deallocate_stock(quantity, commit=commit)
    return stock


@transaction.atomic
def increase_stock(
    variant: "ProductVariant",
    country_code: str,
    quantity: int,
    allocate: bool = False,
    commit: bool = True,
) -> Stock:
    stock = Stock.objects.select_for_update(of=("self",)).get_or_create_for_country(
        country_code, variant
    )
    stock.increase_stock(quantity, allocate=allocate, commit=commit)
    return stock


@transaction.atomic
def decrease_stock(
    variant: "ProductVariant", country_code: str, quantity: int, commit: bool = True
) -> Stock:
    stock = Stock.objects.select_for_update(of=("self",)).get_variant_stock_for_country(
        country_code, variant
    )
    stock.decrease_stock(quantity, commit=commit)
    return stock


@transaction.atomic
def set_stock_quantity(
    variant: "ProductVariant", country_code: str, quantity: int, commit: bool = True
) -> Stock:
    stock = Stock.objects.select_for_update(of=("self",)).get_or_create_for_country(
        country_code, variant
    )
    stock.quantity = quantity
    if commit:
        stock.save(update_fields=["quantity"])
    return stock
