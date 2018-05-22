from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from prices import Money, TaxedMoney

from saleor.cart.checkout import views
from saleor.cart.checkout.forms import NoteForm
from saleor.cart.checkout.utils import get_voucher_discount_for_checkout
from saleor.cart.checkout.core import STORAGE_SESSION_KEY, Checkout
from saleor.core.exceptions import InsufficientStock
from saleor.discount import DiscountValueType, VoucherType
from saleor.discount.models import Voucher, NotApplicable


def test_checkout_version(checkout):
    storage = checkout.for_storage()
    assert storage['version'] == Checkout.VERSION


@pytest.mark.parametrize('storage_data, expected_storage', [
    (
        {'version': Checkout.VERSION, 'new': 1},
        {'version': Checkout.VERSION, 'new': 1}),
    ({'version': 'wrong', 'new': 1}, {'version': Checkout.VERSION}),
    ({'new': 1}, {'version': Checkout.VERSION}),
    ({}, {'version': Checkout.VERSION}),
    (None, {'version': Checkout.VERSION})])
def test_checkout_version_with_from_storage(storage_data, expected_storage):
    checkout = Checkout.from_storage(
        storage_data, Mock(), AnonymousUser(), None, None, 'tracking_code')
    storage = checkout.for_storage()
    assert storage == expected_storage


def test_checkout_clear_storage(checkout):
    checkout.storage['new'] = 1
    checkout.clear_storage()
    assert checkout.storage is None
    assert checkout.modified is True


@pytest.mark.parametrize('cart, status_code, url', [
    (Mock(__len__=Mock(return_value=0)), 302, reverse('cart:index')),
    (
        Mock(
            __len__=Mock(return_value=1),
            is_shipping_required=Mock(return_value=True)),
        302, reverse('cart:checkout-shipping-address')),
    (
        Mock(
            __len__=Mock(return_value=1),
            is_shipping_required=Mock(return_value=False)),
        302, reverse('cart:checkout-summary')),
    (
        Mock(
            __len__=Mock(return_value=0),
            is_shipping_required=Mock(return_value=False)),
        302, reverse('cart:index'))])
def test_index_view(checkout, cart, status_code, url, rf, monkeypatch):
    checkout.cart = cart
    request = rf.get('cart:checkout-index', follow=True)
    request.user = checkout.user
    request.session = {STORAGE_SESSION_KEY: checkout.for_storage()}
    request.discounts = []
    request.taxes = None
    monkeypatch.setattr(
        'saleor.cart.utils.get_cart_from_request', lambda req, qs: cart)
    response = views.index_view(request)
    assert response.status_code == status_code
    assert response.url == url


def test_checkout_discount(checkout_with_items, sale, vatlayer):
    checkout_with_items.discounts = (sale,)
    checkout_with_items.taxes = vatlayer
    assert checkout_with_items.get_total() == TaxedMoney(
        net=Money('4.07', 'USD'), gross=Money('5.00', 'USD'))


def test_checkout_create_order_insufficient_stock(
        checkout, request_cart, customer_user, product):
    product_type = product.product_type
    product_type.is_shipping_required = False
    product_type.save()
    variant = product.variants.get()
    request_cart.add(variant, quantity=10, check_quantity=False)
    checkout.cart = request_cart
    checkout.user = customer_user
    with pytest.raises(InsufficientStock):
        checkout.create_order()


def test_checkout_taxes(checkout_with_items, shipping_method, vatlayer):
    checkout_with_items.taxes = vatlayer
    cart = checkout_with_items.cart
    cart.shipping_method = shipping_method.price_per_country.get()
    cart.save()
    assert checkout_with_items.cart.get_shipping_price(vatlayer) == (
        TaxedMoney(net=Money('8.13', 'USD'), gross=Money(10, 'USD')))
    subtotal = checkout_with_items.cart.get_total(taxes=vatlayer)
    assert checkout_with_items.get_subtotal() == subtotal


@pytest.mark.parametrize('note_value', [
    '',
    '    ',
    '   test_note  ',
    'test_note'])
def test_note_form(checkout, note_value):
    form = NoteForm({'note': note_value}, checkout=checkout)
    form.is_valid()
    form.set_checkout_note()
    assert checkout.note == note_value.strip()


def test_note_in_created_order(checkout_with_items):
    checkout_with_items.note = ''
    order = checkout_with_items.create_order()
    assert not order.notes.all()
    checkout_with_items.note = 'test_note'
    order = checkout_with_items.create_order()
    assert order.notes.filter(content='test_note').exists()


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
        limit=Money(limit, 'USD') if limit is not None else None)
    subtotal = TaxedMoney(net=Money(total, 'USD'), gross=Money(total, 'USD'))
    checkout = Mock(get_subtotal=Mock(return_value=subtotal))
    discount = get_voucher_discount_for_checkout(voucher, checkout)
    assert discount == Money(expected_value, 'USD')


def test_value_voucher_checkout_discount_not_applicable(settings):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        limit=Money(100, 'USD'))
    subtotal = TaxedMoney(net=Money(10, 'USD'), gross=Money(10, 'USD'))
    checkout = Mock(get_subtotal=Mock(return_value=subtotal))
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert e.value.limit == Money(100, 'USD')


@pytest.mark.parametrize(
    'shipping_cost, shipping_country_code, discount_value, discount_type, apply_to, expected_value', [  # noqa
        (10, None, 50, DiscountValueType.PERCENTAGE, None, 5),
        (10, None, 20, DiscountValueType.FIXED, None, 10),
        (10, 'PL', 20, DiscountValueType.FIXED, '', 10),
        (5, 'PL', 5, DiscountValueType.FIXED, 'PL', 5)])
def test_shipping_voucher_checkout_discount(
        settings, shipping_cost, shipping_country_code, discount_value,
        discount_type, apply_to, expected_value):
    subtotal = TaxedMoney(net=Money(100, 'USD'), gross=Money(100, 'USD'))
    shipping_total = TaxedMoney(
        net=Money(shipping_cost, 'USD'), gross=Money(shipping_cost, 'USD'))
    checkout = Mock(
        get_subtotal=Mock(return_value=subtotal),
        cart=Mock(
            is_shipping_required=Mock(return_value=True),
            shipping_method=Mock(
                price=Money(shipping_cost, 'USD'),
                country_code=shipping_country_code,
                get_total_price=Mock(return_value=shipping_total))))
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to,
        limit=None)
    discount = get_voucher_discount_for_checkout(voucher, checkout)
    assert discount == Money(expected_value, 'USD')


@pytest.mark.parametrize(
    'is_shipping_required, shipping_method, discount_value, discount_type, '
    'apply_to, limit, subtotal, error_msg', [
        (True, Mock(country_code='PL'), 10, DiscountValueType.FIXED,
         'US', None, Money(10, 'USD'),
         'This offer is only valid in United States of America.'),
        (True, None, 10, DiscountValueType.FIXED,
         None, None, Money(10, 'USD'),
         'Please select a shipping method first.'),
        (False, None, 10, DiscountValueType.FIXED,
         None, None, Money(10, 'USD'),
         'Your order does not require shipping.'),
        (True, Mock(price=Money(10, 'USD')), 10,
         DiscountValueType.FIXED, None, 5, Money(2, 'USD'),
         'This offer is only valid for orders over $5.00.')])
def test_shipping_voucher_checkout_discount_not_applicable(
        settings, is_shipping_required, shipping_method, discount_value,
        discount_type, apply_to, limit, subtotal, error_msg):
    subtotal_price = TaxedMoney(net=subtotal, gross=subtotal)
    checkout = Mock(
        cart=Mock(
            is_shipping_required=Mock(return_value=is_shipping_required),
            shipping_method=shipping_method),
        get_subtotal=Mock(return_value=subtotal_price))
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Money(limit, 'USD') if limit is not None else None,
        apply_to=apply_to)
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert str(e.value) == error_msg


def test_product_voucher_checkout_discount_not_applicable(
        settings, monkeypatch):
    monkeypatch.setattr(
        'saleor.cart.checkout.utils.get_product_variants_and_prices',
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
        'saleor.cart.checkout.utils.get_category_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.CATEGORY,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'
