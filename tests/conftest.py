import pytest

from saleor.product.models import Product, ProductVariant, Stock
from saleor.userprofile.models import Address


@pytest.fixture
def billing_address(db):  # pylint: disable=W0613
    return Address.objects.create(
        first_name='John', last_name='Doe',
        company_name='Mirumee Software',
        street_address_1='Tęczowa 7',
        city='Wrocław',
        postal_code='53-601',
        country='PL')


@pytest.fixture
def product_in_stock(db):  # pylint: disable=W0613
    product = Product.objects.create(
        name='Test product', price=10, weight=1)
    variant = ProductVariant.objects.create(product=product, sku='123')
    Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=5,
        location='Warehouse 1')
    Stock.objects.create(
        variant=variant, cost_price=100, quantity=5, quantity_allocated=5,
        location='Warehouse 2')
    Stock.objects.create(
        variant=variant, cost_price=10, quantity=5, quantity_allocated=0,
        location='Warehouse 3')
    return product
