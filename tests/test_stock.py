import pytest

from saleor.core.exceptions import InsufficientStock
from saleor.warehouse.availability import (
    are_all_product_variants_in_stock,
    check_stock_quantity,
    products_with_low_stock,
)
from saleor.warehouse.management import (
    allocate_stock,
    deallocate_stock,
    decrease_stock,
    increase_stock,
)
from saleor.warehouse.models import Stock

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


@pytest.mark.parametrize(
    "func, expected_quantity, expected_quantity_allocated",
    (
        (increase_stock, 150, 80),
        (decrease_stock, 50, 30),
        (deallocate_stock, 100, 30),
        (allocate_stock, 100, 130),
    ),
)
def test_changing_stock(product, func, expected_quantity, expected_quantity_allocated):
    stock = Stock.objects.first()
    stock.quantity = 100
    stock.quantity_allocated = 80
    stock.save()
    variant = stock.product_variant
    func(variant, COUNTRY_CODE, 50)
    stock.refresh_from_db()
    assert stock.quantity == expected_quantity
    assert stock.quantity_allocated == expected_quantity_allocated
