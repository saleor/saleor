from mock import Mock
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


@pytest.mark.django_db
def test_stock_selector(product_in_stock):
    variant = product_in_stock.variants.get()
    preferred_stock = variant.select_stockrecord(5)
    assert preferred_stock.quantity_available >= 5


@pytest.fixture
def product_without_shipping(monkeypatch):
    monkeypatch.setattr(
        'saleor.product.models.Product.is_shipping_required',
        Mock(return_value=False))


