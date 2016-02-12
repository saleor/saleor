from decimal import Decimal
from mock import Mock
from prices import FixedDiscount, FractionalDiscount, Price

import pytest
from ..product.models import ProductVariant, Product
from .models import Sale, Voucher, NotApplicable


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
    assert final_price.gross == 0
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FixedDiscount)
    assert applied_discount.amount.gross == 50


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


@pytest.mark.parametrize(
    'total, discount_value, discount_type, limit, expected_value', [
    ('100', 10, Voucher.DISCOUNT_VALUE_FIXED, None, 10),
    ('100.05', 10, Voucher.DISCOUNT_VALUE_PERCENTAGE, 100, 10)])
def test_value_voucher_checkout_discount(settings, total, discount_value,
                                         discount_type, limit, expected_value):
    settings.DEFAULT_CURRENCY = 'USD'
    voucher = Voucher(
        code='unique', type=Voucher.VALUE_TYPE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Price(limit, currency='USD') if limit is not None else None)
    checkout = Mock(cart=Mock(get_total=Mock(
        return_value=Price(total, currency='USD'))))
    discount = voucher.get_discount_for_checkout(checkout)
    assert discount.amount == Price(expected_value, currency='USD')


def test_value_voucher_checkout_discount_not_applicable(settings):
    settings.DEFAULT_CURRENCY = 'USD'
    voucher = Voucher(
        code='unique', type=Voucher.VALUE_TYPE,
        discount_value_type=Voucher.DISCOUNT_VALUE_FIXED,
        discount_value=10,
        limit=100)
    checkout = Mock(cart=Mock(get_total=Mock(
        return_value=Price(10, currency='USD'))))
    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert str(e.value) == 'This offer is only valid for orders over $100.00.'


@pytest.mark.parametrize(
    'shipping_cost, shipping_country_code, discount_value, discount_type, apply_to, expected_value', [  # noqa
        (10, None, 50, Voucher.DISCOUNT_VALUE_PERCENTAGE, None, 5),
        (10, None, 20, Voucher.DISCOUNT_VALUE_FIXED, None, 10),
        (10, 'PL', 20, Voucher.DISCOUNT_VALUE_FIXED, '', 10),
        (5, 'PL', 5, Voucher.DISCOUNT_VALUE_FIXED, 'PL', 5)])
def test_shipping_voucher_checkout_discount(settings, shipping_cost,
                                            shipping_country_code,
                                            discount_value, discount_type,
                                            apply_to, expected_value):
    settings.DEFAULT_CURRENCY = 'USD'
    checkout = Mock(
        is_shipping_required=True, shipping_method=Mock(
            price=Price(shipping_cost, currency='USD'),
            country_code=shipping_country_code))
    voucher = Voucher(
        code='unique', type=Voucher.SHIPPING_TYPE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to)
    discount = voucher.get_discount_for_checkout(checkout)
    assert discount.amount == Price(expected_value, currency='USD')


@pytest.mark.parametrize(
    'is_shipping_required, shipping_method, discount_value, discount_type, apply_to, limit, error_msg', [  # noqa
        (True, Mock(country_code='PL'), 10, Voucher.DISCOUNT_VALUE_FIXED, 'US',
         None, 'This offer is only valid in United States of America.'),
        (True, None, 10, Voucher.DISCOUNT_VALUE_FIXED, None, None,
         'Please select a shipping method first.'),
        (False, None, 10, Voucher.DISCOUNT_VALUE_FIXED, None, None,
         'Your order does not require shipping.'),
        (True, Mock(price=Price(10, currency='USD')), 10,
         Voucher.DISCOUNT_VALUE_FIXED, None, 5,
         'This offer is only valid for shipping over $5.00.')])  # noqa
def test_shipping_voucher_checkout_discountnot_applicable(settings,
                                                          is_shipping_required,
                                                          shipping_method,
                                                          discount_value,
                                                          discount_type,
                                                          apply_to, limit,
                                                          error_msg):
    settings.DEFAULT_CURRENCY = 'USD'
    checkout = Mock(is_shipping_required=is_shipping_required,
                    shipping_method=shipping_method)
    voucher = Voucher(
        code='unique', type=Voucher.SHIPPING_TYPE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Price(limit, currency='USD') if limit is not None else None,
        apply_to=apply_to)
    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert str(e.value) == error_msg


def test_product_voucher_checkout_discount_not_applicable(settings,
                                                          monkeypatch):
    monkeypatch.setattr(
        'saleor.discount.models.get_product_variants_and_prices',
        lambda cart, product: [])
    settings.DEFAULT_CURRENCY = 'USD'
    voucher = Voucher(
        code='unique', type=Voucher.PRODUCT_TYPE,
        discount_value_type=Voucher.DISCOUNT_VALUE_FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())
    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'


def test_category_voucher_checkout_discount_not_applicable(settings,
                                                           monkeypatch):
    monkeypatch.setattr(
        'saleor.discount.models.get_category_variants_and_prices',
        lambda cart, product: [])
    settings.DEFAULT_CURRENCY = 'USD'
    voucher = Voucher(
        code='unique', type=Voucher.CATEGORY_TYPE,
        discount_value_type=Voucher.DISCOUNT_VALUE_FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())
    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'



@pytest.mark.parametrize(
    'prices, discount_value, discount_type, apply_to, expected_value', [
        ([10], 10, Voucher.DISCOUNT_VALUE_FIXED, Voucher.APPLY_TO_ONE_PRODUCT, 10),  # noqa
        ([5], 10, Voucher.DISCOUNT_VALUE_FIXED, Voucher.APPLY_TO_ONE_PRODUCT, 5),  # noqa
        ([5, 5], 10, Voucher.DISCOUNT_VALUE_FIXED, Voucher.APPLY_TO_ONE_PRODUCT, 10),  # noqa
        ([2, 3], 10, Voucher.DISCOUNT_VALUE_FIXED, Voucher.APPLY_TO_ONE_PRODUCT, 5),  # noqa

        ([10, 10], 5, Voucher.DISCOUNT_VALUE_FIXED, Voucher.APPLY_TO_ALL_PRODUCTS, 10),  # noqa
        ([5, 2], 5, Voucher.DISCOUNT_VALUE_FIXED, Voucher.APPLY_TO_ALL_PRODUCTS, 7),  # noqa
        ([10, 10, 10], 5, Voucher.DISCOUNT_VALUE_FIXED, Voucher.APPLY_TO_ALL_PRODUCTS, 15),  # noqa

        ([10], 10, Voucher.DISCOUNT_VALUE_PERCENTAGE, None, 1),
        ([10, 10], 10, Voucher.DISCOUNT_VALUE_PERCENTAGE, None, 2),
    ])
def test_products_voucher_checkout_discount_not(settings, monkeypatch, prices,
                                                discount_value, discount_type,
                                                apply_to, expected_value):
    monkeypatch.setattr(
        'saleor.discount.models.get_product_variants_and_prices',
        lambda cart, product: (
            (None, Price(p, currency='USD')) for p in prices))
    settings.DEFAULT_CURRENCY = 'USD'
    voucher = Voucher(
        code='unique', type=Voucher.PRODUCT_TYPE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to)
    checkout = Mock(cart=Mock())
    discount = voucher.get_discount_for_checkout(checkout)
    assert discount.amount == Price(expected_value, currency='USD')
