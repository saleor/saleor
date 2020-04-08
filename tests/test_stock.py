import pytest

from saleor.core.exceptions import InsufficientStock
from saleor.warehouse.availability import (
    are_all_product_variants_in_stock,
    check_stock_quantity,
    get_available_quantity,
    get_quantity_allocated,
    products_with_low_stock,
)
from saleor.warehouse.management import (
    allocate_stock,
    deallocate_stock,
    decrease_stock,
    increase_stock,
)
from saleor.warehouse.models import Allocation, Stock

COUNTRY_CODE = "US"


def test_stock_for_country(product):
    stock = Stock.objects.get()
    warehouse = stock.warehouse
    assert COUNTRY_CODE in warehouse.countries
    assert stock.warehouse == warehouse

    stock_qs = Stock.objects.for_country(COUNTRY_CODE)
    assert stock_qs.count() == 1
    assert stock_qs.first() == stock


def test_stock_for_country_does_not_exists(product, warehouse):
    shipping_zone = warehouse.shipping_zones.first()
    shipping_zone.countries = [COUNTRY_CODE]
    shipping_zone.save(update_fields=["countries"])
    warehouse.refresh_from_db()
    fake_country_code = "PL"
    assert fake_country_code not in warehouse.countries
    stock_qs = Stock.objects.for_country(fake_country_code)
    assert not stock_qs.exists()


def test_check_stock_quantity_without_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    assert (
        check_stock_quantity(order_line.variant, COUNTRY_CODE, order_line.quantity)
        is None
    )


def test_check_stock_quantity_without_stock(order_line):
    with pytest.raises(InsufficientStock):
        check_stock_quantity(order_line.variant, COUNTRY_CODE, 5)


def test_check_stock_quantity_many_allocations(allocations, variant):
    assert check_stock_quantity(variant, COUNTRY_CODE, 1) is None


def test_check_stock_quantity_many_allocations_out_of_stock(allocations, variant):
    quantity = allocations[0].stock.quantity
    with pytest.raises(InsufficientStock):
        check_stock_quantity(variant, COUNTRY_CODE, quantity)


def test_check_stock_quantity_out_of_stock(allocation, variant):
    quantity = allocation.stock.quantity
    with pytest.raises(InsufficientStock):
        check_stock_quantity(variant, COUNTRY_CODE, quantity)


def test_check_stock_quantity(allocation, variant):
    assert check_stock_quantity(variant, COUNTRY_CODE, 1) is None


def test_are_all_product_variants_in_stock_all_in_stock(stock):
    assert are_all_product_variants_in_stock(
        stock.product_variant.product, COUNTRY_CODE
    )


def test_are_all_product_variants_in_stock_stock_empty(allocation, variant):
    allocation.quantity_allocated = allocation.stock.quantity
    allocation.save(update_fields=["quantity_allocated"])

    assert not are_all_product_variants_in_stock(variant.product, COUNTRY_CODE)


def test_are_all_product_variants_in_stock_lack_of_stocks(variant):
    assert not are_all_product_variants_in_stock(variant.product, COUNTRY_CODE)


def test_products_with_low_stock_one_stock(product, settings):
    settings.LOW_STOCK_THRESHOLD = 70
    stock = Stock.objects.first()
    result = products_with_low_stock()
    assert len(result) == 1
    stock_result = result[0]
    assert (
        stock_result["product_variant__product_id"] == stock.product_variant.product_id
    )
    assert stock_result["warehouse_id"] == stock.warehouse_id
    assert stock_result["total_stock"] == stock.quantity


def test_products_with_low_stock_many_stocks(stock, settings):
    settings.LOW_STOCK_THRESHOLD = 70
    quantity = Stock.objects.all().values_list("quantity", flat=True)
    result = products_with_low_stock()
    assert result[0]["total_stock"] == sum(quantity)


def test_products_with_low_stock_filter_properly(stock, settings):
    quantities = Stock.objects.order_by("quantity").values_list("quantity", flat=True)
    settings.LOW_STOCK_THRESHOLD = quantities[0] + 1
    result = products_with_low_stock()
    assert len(result) == 0


def test_decrease_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    decrease_stock(allocation.order_line, COUNTRY_CODE, 50)

    stock.refresh_from_db()
    assert stock.quantity == 50
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


def test_increase_stock_without_allocate(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    increase_stock(allocation.order_line, COUNTRY_CODE, 50, allocate=False)

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

    increase_stock(allocation.order_line, COUNTRY_CODE, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 130


def test_increase_stock_new_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    increase_stock(order_line, COUNTRY_CODE, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


def test_deallocate_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(allocation.order_line, COUNTRY_CODE, 50)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


def test_allocate_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    allocate_stock(allocation.order_line, COUNTRY_CODE, 20)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 100


def test_allocate_stock_new_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    allocate_stock(order_line, COUNTRY_CODE, 50)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


def test_get_quantity_allocated_without_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    quantity_allocated = get_quantity_allocated(order_line.variant, COUNTRY_CODE)
    assert quantity_allocated == 0


def test_get_quantity_allocated_without_stock(order_line):
    quantity_allocated = get_quantity_allocated(order_line.variant, COUNTRY_CODE)
    assert quantity_allocated == 0


def test_get_quantity_allocated_many_allocations(allocations, variant):
    quantity_allocated = get_quantity_allocated(variant, COUNTRY_CODE)
    assert quantity_allocated == 7


def test_get_quantity_allocated(allocation):
    quantity_allocated = get_quantity_allocated(
        allocation.order_line.variant, COUNTRY_CODE
    )
    assert quantity_allocated == allocation.order_line.quantity


def test_get_available_quantity_without_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    available_quantity = get_available_quantity(order_line.variant, COUNTRY_CODE)
    assert available_quantity == stock.quantity


def test_get_available_quantity_without_stock(order_line):
    available_quantity = get_available_quantity(order_line.variant, COUNTRY_CODE)
    assert available_quantity == 0


def test_get_available_quantity_many_allocations(allocations, variant):
    available_quantity = get_available_quantity(variant, COUNTRY_CODE)
    assert available_quantity == 8


def test_get_available_quantity(allocation):
    available_quantity = get_available_quantity(
        allocation.order_line.variant, COUNTRY_CODE
    )
    assert available_quantity == (
        allocation.stock.quantity - allocation.quantity_allocated
    )
