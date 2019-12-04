import pytest

from saleor.core.exceptions import InsufficientStock
from saleor.stock.models import Stock
from saleor.stock.utils.availability import (
    are_all_product_variants_in_stock,
    check_stock_quantity,
)

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


def test_are_all_product_variants_in_stock_all_in_stock(product):
    assert are_all_product_variants_in_stock(product, COUNTRY_CODE)


def test_are_all_product_variants_in_stock_stock_empty(product):
    stock = Stock.objects.first()
    stock.quantity_allocated = stock.quantity
    stock.save(update_fields=["quantity_allocated"])

    assert not are_all_product_variants_in_stock(product, COUNTRY_CODE)


def test_are_all_product_variants_in_stock_lack_of_stocks(product):
    Stock.objects.all().delete()
    assert not are_all_product_variants_in_stock(product, COUNTRY_CODE)
