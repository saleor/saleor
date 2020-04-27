import pytest
from django.db.models import Sum
from django.db.models.functions import Coalesce

from saleor.core.exceptions import InsufficientStock
from saleor.warehouse.management import (
    allocate_stock,
    deallocate_stock,
    deallocate_stock_for_order,
    decrease_stock,
    increase_stock,
)
from saleor.warehouse.models import Allocation

COUNTRY_CODE = "US"


def test_allocate_stock(order_line, stock):
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    allocate_stock(order_line, COUNTRY_CODE, 50)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


def test_allocate_stock_many_stocks(order_line, variant_with_many_stocks):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    allocate_stock(order_line, COUNTRY_CODE, 5)

    allocations = Allocation.objects.filter(order_line=order_line, stock__in=stocks)
    assert allocations[0].quantity_allocated == 4
    assert allocations[1].quantity_allocated == 1


def test_allocate_stock_many_stocks_partially_allocated(
    order_line, order_line_with_allocation_in_many_stocks
):
    allocated_line = order_line_with_allocation_in_many_stocks
    variant = allocated_line.variant
    stocks = variant.stocks.all()

    allocate_stock(order_line, COUNTRY_CODE, 4)

    allocations = Allocation.objects.filter(order_line=order_line, stock__in=stocks)
    assert allocations[0].quantity_allocated == 2
    assert allocations[1].quantity_allocated == 2


def test_allocate_stock_partially_allocated_insufficient_stocks(
    order_line, order_line_with_allocation_in_many_stocks
):
    allocated_line = order_line_with_allocation_in_many_stocks
    variant = allocated_line.variant
    stocks = variant.stocks.all()

    with pytest.raises(InsufficientStock):
        allocate_stock(order_line, COUNTRY_CODE, 6)

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_allocate_stock_insufficient_stocks(order_line, variant_with_many_stocks):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    with pytest.raises(InsufficientStock):
        allocate_stock(order_line, COUNTRY_CODE, 10)

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_deallocate_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(allocation.order_line, 80)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0


def test_deallocate_stock_partially(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(allocation.order_line, 50)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


def test_deallocate_stock_many_allocations(order_line_with_allocation_in_many_stocks,):
    order_line = order_line_with_allocation_in_many_stocks

    deallocate_stock(order_line, 3)

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0


def test_deallocate_stock_many_allocations_partially(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks

    deallocate_stock(order_line, 1)

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 1
    assert allocations[1].quantity_allocated == 1


def test_increase_stock_without_allocate(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=False)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 80


def test_increase_stock_with_allocate(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 130


def test_increase_stock_with_new_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    increase_stock(order_line, stock.warehouse, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


def test_decrease_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(allocation.order_line, 50, warehouse_pk)

    stock.refresh_from_db()
    assert stock.quantity == 50
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


def test_decrease_stock_partially(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(allocation.order_line, 80, warehouse_pk)

    stock.refresh_from_db()
    assert stock.quantity == 20
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0


def test_decrease_stock_many_allocations(order_line_with_allocation_in_many_stocks,):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[1].stock.warehouse.pk

    decrease_stock(order_line, 3, warehouse_pk)

    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
    assert allocations[0].stock.quantity == 4
    assert allocations[1].stock.quantity == 0


def test_decrease_stock_many_allocations_partially(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[0].stock.warehouse.pk

    decrease_stock(order_line, 2, warehouse_pk)

    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 1
    assert allocations[0].stock.quantity == 2
    assert allocations[1].stock.quantity == 3


def test_decrease_stock_more_then_allocated(order_line_with_allocation_in_many_stocks,):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[0].stock.warehouse.pk
    quantity_allocated = allocations.aggregate(
        quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
    )["quantity_allocated"]
    assert quantity_allocated < 4

    decrease_stock(order_line, 4, warehouse_pk)

    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
    assert allocations[0].stock.quantity == 0
    assert allocations[1].stock.quantity == 3


def test_deallocate_stock_for_order(order_line_with_allocation_in_many_stocks,):
    order_line = order_line_with_allocation_in_many_stocks
    order = order_line.order

    deallocate_stock_for_order(order)

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
