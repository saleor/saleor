from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from prices import Money, TaxedMoney

from saleor.account.models import Address
from saleor.checkout import views
from saleor.checkout.core import STORAGE_SESSION_KEY, Checkout
from saleor.checkout.forms import NoteForm
from saleor.checkout.utils import get_voucher_discount_for_checkout
from saleor.core.exceptions import InsufficientStock
from saleor.discount import DiscountValueType, VoucherType
from saleor.discount.models import Voucher, NotApplicable
from saleor.shipping.models import ShippingMethodCountry


def test_checkout_version():
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
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
        storage_data, Mock(), AnonymousUser(), 'tracking_code')
    storage = checkout.for_storage()
    assert storage == expected_storage


def test_checkout_clear_storage():
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.storage['new'] = 1
    checkout.clear_storage()
    assert checkout.storage is None
    assert checkout.modified is True


def test_checkout_is_shipping_required():
    cart = Mock(is_shipping_required=Mock(return_value=True))
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    assert checkout.is_shipping_required is True


@pytest.mark.parametrize('user, shipping', [
    (Mock(default_shipping_address='user_shipping'), 'user_shipping'),
    (AnonymousUser(), None)])
def test_checkout_shipping_address_with_anonymous_user(user, shipping):
    checkout = Checkout(Mock(), user, 'tracking_code')
    assert checkout._shipping_address is None
    assert checkout.shipping_address == shipping
    assert checkout._shipping_address == shipping


@pytest.mark.parametrize('address_objects, shipping', [
    (Mock(get=Mock(return_value='shipping')), 'shipping'),
    (Mock(get=Mock(side_effect=Address.DoesNotExist)), None)])
def test_checkout_shipping_address_with_storage(
        address_objects, shipping, monkeypatch):
    monkeypatch.setattr(
        'saleor.checkout.core.Address.objects', address_objects)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_address'] = {'id': 1}
    assert checkout.shipping_address == shipping


def test_checkout_shipping_address_setter():
    address = Address(first_name='Jan', last_name='Kowalski')
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    assert checkout._shipping_address is None
    checkout.shipping_address = address
    assert checkout._shipping_address == address
    assert checkout.storage['shipping_address'] == {
        'city': '',
        'city_area': '',
        'company_name': '',
        'country': '',
        'country_area': '',
        'first_name': 'Jan',
        'id': None,
        'last_name': 'Kowalski',
        'phone': '',
        'postal_code': '',
        'street_address_1': '',
        'street_address_2': ''}


@pytest.mark.parametrize('shipping_address, shipping_method, value', [
    (
        Mock(country=Mock(code='PL')),
        Mock(
            country_code='PL',
            __eq__=lambda n, o: n.country_code == o.country_code),
        Mock(country_code='PL')),
    (Mock(country=Mock(code='DE')), Mock(country_code='PL'), None),
    (None, Mock(country_code='PL'), None)])
def test_checkout_shipping_method(
        shipping_address, shipping_method, value, monkeypatch):
    queryset = Mock(get=Mock(return_value=shipping_method))
    monkeypatch.setattr(Checkout, 'shipping_address', shipping_address)
    monkeypatch.setattr(
        'saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_method_country_id'] = 1
    assert checkout._shipping_method is None
    assert checkout.shipping_method == value
    assert checkout._shipping_method == value


def test_checkout_shipping_does_not_exists(monkeypatch):
    queryset = Mock(get=Mock(side_effect=ShippingMethodCountry.DoesNotExist))
    monkeypatch.setattr(
        'saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_method_country_id'] = 1
    assert checkout.shipping_method is None


def test_checkout_shipping_method_setter():
    shipping_method = Mock(id=1)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    assert checkout.modified is False
    assert checkout._shipping_method is None
    checkout.shipping_method = shipping_method
    assert checkout._shipping_method == shipping_method
    assert checkout.modified is True
    assert checkout.storage['shipping_method_country_id'] == 1


@pytest.mark.parametrize('user, address', [
    (AnonymousUser(), None),
    (
        Mock(
            default_billing_address='billing_address',
            addresses=Mock(
                is_authenticated=Mock(return_value=True))),
        'billing_address')])
def test_checkout_billing_address(user, address):
    checkout = Checkout(Mock(), user, 'tracking_code')
    assert checkout.billing_address == address


@pytest.mark.parametrize('cart, status_code, url', [
    (Mock(__len__=Mock(return_value=0)), 302, reverse('cart:index')),
    (
        Mock(
            __len__=Mock(return_value=1),
            is_shipping_required=Mock(return_value=True)),
        302, reverse('checkout:shipping-address')),
    (
        Mock(
            __len__=Mock(return_value=1),
            is_shipping_required=Mock(return_value=False)),
        302, reverse('checkout:summary')),
    (
        Mock(
            __len__=Mock(return_value=0),
            is_shipping_required=Mock(return_value=False)),
        302, reverse('cart:index'))])
def test_index_view(cart, status_code, url, rf, monkeypatch):
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    request = rf.get('checkout:index', follow=True)
    request.user = checkout.user
    request.session = {STORAGE_SESSION_KEY: checkout.for_storage()}
    request.discounts = []
    monkeypatch.setattr(
        'saleor.cart.utils.get_cart_from_request', lambda req, qs: cart)
    response = views.index_view(request)
    assert response.status_code == status_code
    assert response.url == url


def test_checkout_discount(checkout_with_items, sale):
    assert checkout_with_items.get_total() == TaxedMoney(
        net=Money(5, 'USD'), gross=Money(5, 'USD'))


def test_checkout_create_order_insufficient_stock(
        request_cart, customer_user, product_in_stock):
    product_type = product_in_stock.product_type
    product_type.is_shipping_required = False
    product_type.save()
    variant = product_in_stock.variants.get()
    request_cart.add(variant, quantity=10, check_quantity=False)
    checkout = Checkout(request_cart, customer_user, 'tracking_code')
    with pytest.raises(InsufficientStock):
        checkout.create_order()


@pytest.mark.parametrize('note_value', [
    '',
    '    ',
    '   test_note  ',
    'test_note'])
def test_note_form(note_value):
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
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
        is_shipping_required=True, shipping_method=Mock(
            price=Money(shipping_cost, 'USD'),
            country_code=shipping_country_code,
            get_total_price=Mock(return_value=shipping_total)))
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
        is_shipping_required=is_shipping_required,
        shipping_method=shipping_method,
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
        'saleor.checkout.utils.get_product_variants_and_prices',
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
        'saleor.checkout.utils.get_category_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.CATEGORY,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'
