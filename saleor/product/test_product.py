import pytest

from . import models


@pytest.fixture
def product_in_stock(db):
    product = models.Product.objects.create(
        name='Test product', price=10, weight=1)
    variant = models.ProductVariant.objects.create(product=product, sku='123')
    models.Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=5,
        location='Warehouse 1')
    models.Stock.objects.create(
        variant=variant, cost_price=100, quantity=5, quantity_allocated=5,
        location='Warehouse 2')
    models.Stock.objects.create(
        variant=variant, cost_price=10, quantity=5, quantity_allocated=0,
        location='Warehouse 3')
    return product


def test_stock_selector(product_in_stock):
    variant = product_in_stock.variants.get()
    preferred_stock = variant.select_stockrecord(5)
    assert preferred_stock.quantity_available >= 5


def test_stock_allocator(product_in_stock):
    variant = product_in_stock.variants.get()
    stock = variant.select_stockrecord(5)
    assert stock.quantity_allocated == 0
    models.Stock.objects.allocate_stock(stock, 1)
    stock = models.Stock.objects.get(pk=stock.pk)
    assert stock.quantity_allocated == 1
