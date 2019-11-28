import pytest

from saleor.core.exceptions import InsufficientStock
from saleor.stock.models import Stock
from saleor.stock.stock_management import check_stock_quantity

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
    fake_country_code = "OO"
    assert fake_country_code not in warehouse.countries
    stock_qs = Stock.objects.for_country(fake_country_code)
    assert not stock_qs.exists()


def test_check_stock_quantity_is_lower_than_available(product):
    stock = Stock.objects.get()
    variant = stock.product_variant
    new_quantity = stock.quantity_available
    assert check_stock_quantity(variant, COUNTRY_CODE, new_quantity) is None


def test_check_stock_quantity_is_not_sufficient(product):
    stock = Stock.objects.get()
    variant = stock.product_variant
    new_quantity = stock.quantity_available + 1
    with pytest.raises(InsufficientStock):
        check_stock_quantity(variant, COUNTRY_CODE, new_quantity)
