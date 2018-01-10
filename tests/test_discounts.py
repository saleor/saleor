from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from saleor.discount import (
    DiscountValueType, VoucherApplyToProduct, VoucherType)
from saleor.discount.forms import CheckoutDiscountForm
from saleor.discount.models import NotApplicable, Sale, Voucher
from saleor.discount.utils import (
    decrease_voucher_usage, increase_voucher_usage,
    get_product_discount_on_sale, get_voucher_discount_for_checkout)
from saleor.product.models import Product, ProductVariant


@pytest.mark.parametrize('limit, value', [
    (Money(5, currency='USD'), Money(10, currency='USD')),
    (Money(10, currency='USD'), Money(10, currency='USD'))])
def test_valid_voucher_limit(settings, limit, value):
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=Money(10, currency='USD'),
        limit=limit)
    voucher.validate_limit(TaxedMoney(net=value, gross=value))


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_variant_discounts(product_in_stock):
    variant = product_in_stock.variants.get()
    low_discount = Sale.objects.create(
        type=DiscountValueType.FIXED,
        value=5)
    low_discount.products.add(product_in_stock)
    discount = Sale.objects.create(
        type=DiscountValueType.FIXED,
        value=8)
    discount.products.add(product_in_stock)
    high_discount = Sale.objects.create(
        type=DiscountValueType.FIXED,
        value=50)
    high_discount.products.add(product_in_stock)
    final_price = variant.get_price_per_item(discounts=Sale.objects.all())
    assert final_price.gross == Money(0, currency='USD')


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(product_in_stock):
    variant = product_in_stock.variants.get()
    discount = Sale.objects.create(
        type=DiscountValueType.PERCENTAGE,
        value=50)
    discount.products.add(product_in_stock)
    final_price = variant.get_price_per_item(discounts=[discount])
    assert final_price.gross == Money(5, 'USD')


@pytest.mark.parametrize(
    'total, discount_value, discount_type, limit, expected_value', [
        ('100', 10, DiscountValueType.FIXED, None, 10),
        ('100.05', 10, DiscountValueType.PERCENTAGE, 100, 10)])
def test_value_voucher_checkout_discount(
        settings, total, discount_value, discount_type, limit, expected_value):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Money(limit, currency='USD') if limit is not None else None)
    subtotal = TaxedMoney(
        net=Money(total, currency='USD'), gross=Money(total, currency='USD'))
    checkout = Mock(get_subtotal=Mock(return_value=subtotal))
    discount = get_voucher_discount_for_checkout(voucher, checkout)
    assert discount == Money(expected_value, currency='USD')


def test_value_voucher_checkout_discount_not_applicable(settings):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        limit=Money(100, currency='USD'))
    subtotal = TaxedMoney(
        net=Money(10, currency='USD'), gross=Money(10, currency='USD'))
    checkout = Mock(get_subtotal=Mock(return_value=subtotal))
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert e.value.limit == Money(100, currency='USD')


@pytest.mark.parametrize(
    'shipping_cost, shipping_country_code, discount_value, discount_type, apply_to, expected_value', [  # noqa
        (10, None, 50, DiscountValueType.PERCENTAGE, None, 5),
        (10, None, 20, DiscountValueType.FIXED, None, 10),
        (10, 'PL', 20, DiscountValueType.FIXED, '', 10),
        (5, 'PL', 5, DiscountValueType.FIXED, 'PL', 5)])
def test_shipping_voucher_checkout_discount(
        settings, shipping_cost, shipping_country_code, discount_value,
        discount_type, apply_to, expected_value):
    subtotal = TaxedMoney(
        net=Money(100, currency='USD'), gross=Money(100, currency='USD'))
    shipping_total = TaxedMoney(
        net=Money(shipping_cost, currency='USD'),
        gross=Money(shipping_cost, currency='USD'))
    checkout = Mock(
        get_subtotal=Mock(return_value=subtotal),
        is_shipping_required=True, shipping_method=Mock(
            price=Money(shipping_cost, currency='USD'),
            country_code=shipping_country_code,
            get_total_price=Mock(return_value=shipping_total)))
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to,
        limit=None)
    discount = get_voucher_discount_for_checkout(voucher, checkout)
    assert discount == Money(expected_value, currency='USD')


@pytest.mark.parametrize(
    'is_shipping_required, shipping_method, discount_value, discount_type, '
    'apply_to, limit, subtotal, error_msg', [
        (True, Mock(country_code='PL'), 10, DiscountValueType.FIXED,
         'US', None, Money(10, currency='USD'),
         'This offer is only valid in United States of America.'),
        (True, None, 10, DiscountValueType.FIXED,
         None, None, Money(10, currency='USD'),
         'Please select a shipping method first.'),
        (False, None, 10, DiscountValueType.FIXED,
         None, None, Money(10, currency='USD'),
         'Your order does not require shipping.'),
        (True, Mock(price=Money(10, currency='USD')), 10,
         DiscountValueType.FIXED, None, 5, Money(2, currency='USD'),
         'This offer is only valid for orders over $5.00.')])
def test_shipping_voucher_checkout_discount_not_applicable(
        settings, is_shipping_required, shipping_method, discount_value,
        discount_type, apply_to, limit, subtotal, error_msg):
    subtotal_price = TaxedMoney(net=subtotal, gross=subtotal)
    checkout = Mock(
        is_shipping_required=is_shipping_required,
        shipping_method=shipping_method,
        get_subtotal=Mock(return_value=subtotal_price))
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Money(limit, currency='USD') if limit is not None else None,
        apply_to=apply_to)
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert str(e.value) == error_msg


def test_product_voucher_checkout_discount_not_applicable(
        settings, monkeypatch):
    monkeypatch.setattr(
        'saleor.discount.utils.get_product_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())

    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'


def test_category_voucher_checkout_discount_not_applicable(
        settings, monkeypatch):
    monkeypatch.setattr(
        'saleor.discount.utils.get_category_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.CATEGORY,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'


def test_invalid_checkout_discount_form(monkeypatch, voucher):
    checkout = Mock(cart=Mock())
    form = CheckoutDiscountForm({'voucher': voucher.code}, checkout=checkout)
    monkeypatch.setattr(
        'saleor.discount.forms.get_voucher_discount_for_checkout',
        Mock(side_effect=NotApplicable('Not applicable')))
    assert not form.is_valid()
    assert 'voucher' in form.errors


def test_voucher_queryset_active(voucher):
    vouchers = Voucher.objects.all()
    assert len(vouchers) == 1
    active_vouchers = Voucher.objects.active(
        date=date.today() - timedelta(days=1))
    assert len(active_vouchers) == 0


def test_checkout_discount_form_active_queryset_voucher_not_active(voucher):
    assert len(Voucher.objects.all()) == 1
    checkout = Mock(cart=Mock())
    voucher.start_date = date.today() + timedelta(days=1)
    voucher.save()
    form = CheckoutDiscountForm({'voucher': voucher.code}, checkout=checkout)
    qs = form.fields['voucher'].queryset
    assert len(qs) == 0


def test_checkout_discount_form_active_queryset_voucher_active(voucher):
    assert len(Voucher.objects.all()) == 1
    checkout = Mock(cart=Mock())
    voucher.start_date = date.today()
    voucher.save()
    form = CheckoutDiscountForm({'voucher': voucher.code}, checkout=checkout)
    qs = form.fields['voucher'].queryset
    assert len(qs) == 1


def test_checkout_discount_form_active_queryset_after_some_time(voucher):
    assert len(Voucher.objects.all()) == 1
    checkout = Mock(cart=Mock())
    voucher.start_date = date(year=2016, month=6, day=1)
    voucher.end_date = date(year=2016, month=6, day=2)
    voucher.save()

    with freeze_time('2016-05-31'):
        form = CheckoutDiscountForm(
            {'voucher': voucher.code}, checkout=checkout)
        assert len(form.fields['voucher'].queryset) == 0

    with freeze_time('2016-06-01'):
        form = CheckoutDiscountForm(
            {'voucher': voucher.code}, checkout=checkout)
        assert len(form.fields['voucher'].queryset) == 1

    with freeze_time('2016-06-03'):
        form = CheckoutDiscountForm(
            {'voucher': voucher.code}, checkout=checkout)
        assert len(form.fields['voucher'].queryset) == 0


@pytest.mark.parametrize(
    'prices, discount_value, discount_type, apply_to, expected_value', [
        (
            [10], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 10),
        (
            [5], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 5),
        (
            [5, 5], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 10),
        (
            [2, 3], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 5),

        (
            [10, 10], 5, DiscountValueType.FIXED,
            VoucherApplyToProduct.ALL_PRODUCTS, 10),
        (
            [5, 2], 5, DiscountValueType.FIXED,
            VoucherApplyToProduct.ALL_PRODUCTS, 7),
        (
            [10, 10, 10], 5, DiscountValueType.FIXED,
            VoucherApplyToProduct.ALL_PRODUCTS, 15),

        ([10], 10, DiscountValueType.PERCENTAGE, None, 1),
        ([10, 10], 10, DiscountValueType.PERCENTAGE, None, 2)])
def test_products_voucher_checkout_discount_not(
        settings, monkeypatch, prices, discount_value, discount_type, apply_to,
        expected_value):
    monkeypatch.setattr(
        'saleor.discount.utils.get_product_variants_and_prices',
        lambda cart, product: (
            (None, TaxedMoney(
                net=Money(p, currency='USD'), gross=Money(p, currency='USD')))
            for p in prices))
    voucher = Voucher(
        code='unique', type=VoucherType.PRODUCT,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to)
    checkout = Mock(cart=Mock())
    discount = get_voucher_discount_for_checkout(voucher, checkout)
    assert discount == Money(expected_value, 'USD')


@pytest.mark.django_db
def test_sale_applies_to_correct_products(product_type, default_category):
    product = Product.objects.create(
        name='Test Product', price=Money(10, currency='USD'), description='',
        pk=10, product_type=product_type, category=default_category)
    variant = ProductVariant.objects.create(product=product, sku='firstvar')
    product2 = Product.objects.create(
        name='Second product', price=Money(15, currency='USD'), description='',
        product_type=product_type, category=default_category)
    sec_variant = ProductVariant.objects.create(
        product=product2, sku='secvar', pk=10)
    sale = Sale.objects.create(
        name='Test sale', value=3, type=DiscountValueType.FIXED)
    sale.products.add(product)
    assert product2 not in sale.products.all()
    product_discount = get_product_discount_on_sale(sale, variant.product)
    discounted_price = product_discount(product.price)
    assert discounted_price == Money(7, currency='USD')
    with pytest.raises(NotApplicable):
        get_product_discount_on_sale(sale, sec_variant.product)


def test_increase_voucher_usage():
    voucher = Voucher.objects.create(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10, usage_limit=100)
    increase_voucher_usage(voucher)
    voucher.refresh_from_db()
    assert voucher.used == 1


def test_decrease_voucher_usage():
    voucher = Voucher.objects.create(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=VoucherType.VALUE,
        discount_value=10, usage_limit=100, used=10)
    decrease_voucher_usage(voucher)
    voucher.refresh_from_db()
    assert voucher.used == 9
