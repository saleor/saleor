from decimal import Decimal
from prices import FixedDiscount, FractionalDiscount

import pytest
from ..product.models import ProductVariant, Product
from .models import Sale


@pytest.fixture
def product():
    return Product.objects.create(
        name='test product',
        description='test description',
        price=10,
        weight=1)


@pytest.fixture
def product_variant(product):
    return ProductVariant.objects.create(
        product=product,
        sku='TESTSKU',
        name='variant')


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_variant_discounts(product_variant):
    product = product_variant.product
    low_discount = Sale.objects.create(
        type=Sale.FIXED,
        value=5)
    low_discount.products.add(product)
    discount = Sale.objects.create(
        type=Sale.FIXED,
        value=8)
    discount.products.add(product)
    high_discount = Sale.objects.create(
        type=Sale.FIXED,
        value=50)
    high_discount.products.add(product)
    final_price = product_variant.get_price_per_item(
        discounts=Sale.objects.all())
    assert final_price.gross == 2
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FixedDiscount)
    assert applied_discount.amount.gross == 8


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(product_variant):
    discount = Sale.objects.create(
        type=Sale.PERCENTAGE,
        value=50)
    discount.products.add(product_variant.product)
    final_price = product_variant.get_price_per_item(discounts=[discount])
    assert final_price.gross == 5
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FractionalDiscount)
    assert applied_discount.factor == Decimal('0.5')
