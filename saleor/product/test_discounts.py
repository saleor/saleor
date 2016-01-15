from decimal import Decimal
from prices import FixedDiscount, FractionalDiscount

import pytest
from . import models


@pytest.fixture
def product():
    return models.Product.objects.create(
        name='test product',
        description='test description',
        price=10,
        weight=1)


@pytest.fixture
def product_variant(product):
    return models.ProductVariant.objects.create(
        product=product,
        sku='TESTSKU',
        name='variant')


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_variant_discounts(product_variant):
    product = product_variant.product
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
    final_price = product_variant.get_price_per_item(
        discounts=models.Discount.objects.all())
    assert final_price.gross == 2
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FixedDiscount)
    assert applied_discount.amount.gross == 8


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(product_variant):
    discount = models.Discount.objects.create(
        type=models.Discount.PERCENTAGE,
        value=50)
    discount.products.add(product_variant.product)
    final_price = product_variant.get_price_per_item(discounts=[discount])
    assert final_price.gross == 5
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FractionalDiscount)
    assert applied_discount.factor == Decimal('0.5')
