import mock
import pytest
from .models import (FixedProductDiscount, get_product_discounts, Product,
                     ProductVariant)


@pytest.fixture(scope='module')
@mock.patch.object(Product, 'variants', create=True)
def test_product(variants_manager):
    product = Product(name='Foo', price=100)
    variants_manager.all.return_value = []
    return product


@mock.patch.object(FixedProductDiscount, 'products', create=True)
def test_product_discounts(mock_discount, test_product):
    mock_discount.all.return_value = [test_product]
    discount = FixedProductDiscount(name='test', discount=10)
    applied_discounts = list(get_product_discounts(test_product, [discount]))
    assert len(applied_discounts) == 1
    assert applied_discounts[0].amount.gross == 10


@mock.patch.object(FixedProductDiscount, 'products', create=True)
@mock.patch.object(Product, 'variants', create=True)
def test_product_variants_discounts(variants_manager, mock_discount, test_product):
    variant = ProductVariant(
        sku='0001', name='first variant', product=test_product)
    variants_manager.all.return_value = [variant]
    test_product.variants = variants_manager
    mock_discount.all.return_value = [test_product]
    discount = FixedProductDiscount(name='test', discount=10)
    applied_discounts = list(
        get_product_discounts(test_product.variants.all()[0], [discount]))
    assert len(applied_discounts) == 1
    assert applied_discounts[0].amount.gross == 10


@mock.patch.object(FixedProductDiscount, 'products', create=True)
@mock.patch.object(Product, 'variants', create=True)
def test_discount_not_applicable(variants_manager, mock_discount, test_product):
    variant = ProductVariant(
        sku='0001', name='first variant', product=test_product)
    variants_manager.all.return_value = [variant]
    test_product.variants = variants_manager
    mock_discount.all.return_value = [test_product]
    discount = FixedProductDiscount(name='test', discount=150)
    applied_discounts = list(
        get_product_discounts(test_product.variants.all()[0], [discount]))
    assert len(applied_discounts) == 0


@mock.patch.object(FixedProductDiscount, 'products', create=True)
@mock.patch.object(Product, 'variants', create=True)
def test_only_applicable_discounts(variants_manager, mock_discount, test_product):
    variant = ProductVariant(
        sku='0001', name='first variant', product=test_product)
    variants_manager.all.return_value = [variant]
    test_product.variants = variants_manager
    mock_discount.all.return_value = [test_product]
    discounts = [FixedProductDiscount(name='test', discount=10),
                 FixedProductDiscount(name='test2', discount=90),
                 FixedProductDiscount(name='test2', discount=120)]
    applied_discounts = list(
        get_product_discounts(test_product.variants.all()[0], discounts))
    assert len(applied_discounts) == 2
