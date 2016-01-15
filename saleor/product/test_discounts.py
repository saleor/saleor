from decimal import Decimal
from prices import FixedDiscount, FractionalDiscount

import pytest
from . import models


@pytest.fixture
def test_product():
    return models.Product.objects.create(
        name='test product',
        description='test description',
        price=10,
        weight=1)


@pytest.fixture
def test_product_variant(test_product):
    return models.ProductVariant.objects.create(
        product=test_product,
        sku='TESTSKU',
        name='variant')


@pytest.mark.django_db(transaction=True)
def test_variant_discounts(test_product_variant):
    variant = test_product_variant
    product = variant.product
    low_discount = models.Discount.objects.create(
        type=models.Discount.FIXED,
        value=5)
    low_discount.products.add(product)
    discount = models.Discount.objects.create(
        type=models.Discount.FIXED,
        value=8)
    discount.products.add(product)
    high_discount = models.Discount.objects.create(
        type=models.Discount.FIXED,
        value=50)
    high_discount.products.add(product)
    final_price = variant.get_price_per_item(
        discounts=[low_discount, discount, high_discount])
    assert final_price.gross == 2
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FixedDiscount)
    assert applied_discount.amount.gross == 8


@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(test_product_variant):
    variant = test_product_variant
    product = variant.product
    discount = models.Discount.objects.create(
        type=models.Discount.PERCENTAGE,
        value=50)
    discount.products.add(product)
    final_price = variant.get_price_per_item(discounts=[discount])
    assert final_price.gross == 5
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FractionalDiscount)
    assert applied_discount.factor == Decimal('0.5')
