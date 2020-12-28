import pytest

from ...core.exceptions import InsufficientStock
from ..availability import (
    are_all_product_variants_in_stock,
    check_stock_quantity,
    get_available_quantity,
    get_quantity_allocated,
)
from ..models import Allocation

COUNTRY_CODE = "US"


def test_check_stock_quantity(variant_with_many_stocks):
    assert check_stock_quantity(variant_with_many_stocks, COUNTRY_CODE, 7) is None


def test_check_stock_quantity_out_of_stock(variant_with_many_stocks):
    with pytest.raises(InsufficientStock):
        check_stock_quantity(variant_with_many_stocks, COUNTRY_CODE, 8)


def test_check_stock_quantity_with_allocations(
    variant_with_many_stocks,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
):
    assert check_stock_quantity(variant_with_many_stocks, COUNTRY_CODE, 3) is None


def test_check_stock_quantity_with_allocations_out_of_stock(
    variant_with_many_stocks, order_line_with_allocation_in_many_stocks
):
    with pytest.raises(InsufficientStock):
        check_stock_quantity(variant_with_many_stocks, COUNTRY_CODE, 5)


def test_check_stock_quantity_without_stocks(variant_with_many_stocks):
    variant_with_many_stocks.stocks.all().delete()
    with pytest.raises(InsufficientStock):
        check_stock_quantity(variant_with_many_stocks, COUNTRY_CODE, 1)


def test_check_stock_quantity_without_one_stock(variant_with_many_stocks):
    variant_with_many_stocks.stocks.get(quantity=3).delete()
    assert check_stock_quantity(variant_with_many_stocks, COUNTRY_CODE, 4) is None


def test_get_available_quantity_without_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    available_quantity = get_available_quantity(order_line.variant, COUNTRY_CODE)
    assert available_quantity == stock.quantity


def test_get_available_quantity(variant_with_many_stocks):
    available_quantity = get_available_quantity(variant_with_many_stocks, COUNTRY_CODE)
    assert available_quantity == 7


def test_get_available_quantity_with_allocations(
    variant_with_many_stocks,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
):
    available_quantity = get_available_quantity(variant_with_many_stocks, COUNTRY_CODE)
    assert available_quantity == 3


def test_get_available_quantity_without_stocks(variant_with_many_stocks):
    variant_with_many_stocks.stocks.all().delete()
    available_quantity = get_available_quantity(variant_with_many_stocks, COUNTRY_CODE)
    assert available_quantity == 0


def test_get_quantity_allocated(
    variant_with_many_stocks, order_line_with_allocation_in_many_stocks
):
    quantity_allocated = get_quantity_allocated(variant_with_many_stocks, COUNTRY_CODE)
    assert quantity_allocated == 3


def test_get_quantity_allocated_without_allocation(variant_with_many_stocks):
    quantity_allocated = get_quantity_allocated(variant_with_many_stocks, COUNTRY_CODE)
    assert quantity_allocated == 0


def test_get_quantity_allocated_without_stock(variant_with_many_stocks):
    variant_with_many_stocks.stocks.all().delete()
    quantity_allocated = get_quantity_allocated(variant_with_many_stocks, COUNTRY_CODE)
    assert quantity_allocated == 0


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


def test_are_all_product_variants_in_stock_warehouse_without_stock(
    variant_with_many_stocks,
):
    variant_with_many_stocks.stocks.first().delete()
    assert are_all_product_variants_in_stock(
        variant_with_many_stocks.product, COUNTRY_CODE
    )
