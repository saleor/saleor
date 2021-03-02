import pytest

from ...core.exceptions import InsufficientStock
from ..availability import (
    check_stock_quantity,
    check_stock_quantity_bulk,
    get_available_quantity,
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


def test_check_stock_quantity_bulk(variant_with_many_stocks):
    variant = variant_with_many_stocks
    country_code = "US"
    available_quantity = get_available_quantity(variant, country_code)

    # test that it doesn't raise error for available quantity
    assert (
        check_stock_quantity_bulk(
            [variant_with_many_stocks], country_code, [available_quantity]
        )
        is None
    )

    # test that it raises an error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_stock_quantity_bulk(
            [variant_with_many_stocks], country_code, [available_quantity + 1]
        )

    # test that it raises an error if no stocks are found
    variant.stocks.all().delete()
    with pytest.raises(InsufficientStock):
        check_stock_quantity_bulk(
            [variant_with_many_stocks], country_code, [available_quantity]
        )
