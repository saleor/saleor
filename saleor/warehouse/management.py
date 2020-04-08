from typing import TYPE_CHECKING

from django.db import transaction

from .models import Allocation, Stock

if TYPE_CHECKING:
    from ..order.models import OrderLine
    from ..product.models import ProductVariant


def _allocate_stock(stock: Stock, order_line: "OrderLine", quantity: int) -> Allocation:
    allocation = (
        stock.allocations.select_for_update(of=("self",))
        .filter(order_line=order_line)
        .first()
    )
    if allocation:
        allocation.allocate_stock(quantity, commit=True)
    else:
        allocation = Allocation.objects.create(
            order_line=order_line, stock=stock, quantity_allocated=quantity
        )
    return allocation


def _deallocate_stock(
    stock: Stock, order_line: "OrderLine", quantity: int
) -> Allocation:
    allocation = stock.allocations.select_for_update(of=("self",)).get(
        order_line=order_line
    )
    allocation.deallocate_stock(quantity, commit=True)
    return allocation


@transaction.atomic
def allocate_stock(
    order_line: "OrderLine", country_code: str, quantity: int
) -> Allocation:
    stock = Stock.objects.select_for_update(of=("self",)).get_variant_stock_for_country(
        country_code, order_line.variant
    )
    return _allocate_stock(stock, order_line, quantity)


@transaction.atomic
def deallocate_stock(
    order_line: "OrderLine", country_code: str, quantity: int
) -> Allocation:
    stock = Stock.objects.get_variant_stock_for_country(
        country_code, order_line.variant
    )
    return _deallocate_stock(stock, order_line, quantity)


@transaction.atomic
def increase_stock(
    order_line: "OrderLine", country_code: str, quantity: int, allocate: bool = False,
) -> Stock:
    stock = Stock.objects.select_for_update(of=("self",)).get_or_create_for_country(
        country_code, order_line.variant
    )
    stock.increase_stock(quantity, commit=True)
    if allocate:
        _allocate_stock(stock, order_line, quantity)
    return stock


@transaction.atomic
def decrease_stock(order_line: "OrderLine", country_code: str, quantity: int) -> Stock:
    stock = Stock.objects.select_for_update(of=("self",)).get_variant_stock_for_country(
        country_code, order_line.variant
    )
    stock.decrease_stock(quantity, commit=True)
    _deallocate_stock(stock, order_line, quantity)
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
