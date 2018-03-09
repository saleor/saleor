from unittest.mock import MagicMock, Mock

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from prices import Money, TaxedMoney

from saleor.account.models import Address
from saleor.checkout import views
from saleor.checkout.core import STORAGE_SESSION_KEY, Checkout
from saleor.checkout.forms import NoteForm
from saleor.core.exceptions import InsufficientStock
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


def test_checkout_deliveries():
    item_price = TaxedMoney(net=Money(10, 'USD'), gross=Money(10, 'USD'))
    partition = Mock(
        get_total=Mock(return_value=item_price),
        get_price_per_item=Mock(return_value=item_price))

    def f():
        yield partition

    partition.__iter__ = Mock(return_value=f())
    cart = Mock(partition=Mock(return_value=[partition]), currency='USD')
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    deliveries = list(checkout.deliveries)
    assert deliveries[0][1] == TaxedMoney(
        net=Money(0, 'USD'), gross=Money(0, 'USD'))
    assert deliveries[0][2] == partition.get_total()
    assert deliveries[0][0][0][0] == partition


def test_checkout_deliveries_with_shipping_method(monkeypatch):
    shipping_cost = Money(3, settings.DEFAULT_CURRENCY)
    items_cost = Money(5, settings.DEFAULT_CURRENCY)
    cost_with_shipping = items_cost + shipping_cost

    items_price = TaxedMoney(net=items_cost, gross=items_cost)
    partition = Mock(
        is_shipping_required=MagicMock(return_value=True),
        get_total=Mock(return_value=items_price),
        get_price_per_item=Mock(return_value=items_price))

    def f():
        yield partition

    partition.__iter__ = Mock(return_value=f())
    cart = Mock(
        partition=Mock(return_value=[partition]),
        currency=settings.DEFAULT_CURRENCY)

    shipping_price = TaxedMoney(net=shipping_cost, gross=shipping_cost)
    shipping_method_mock = Mock(
        get_total_price=Mock(return_value=shipping_price))
    monkeypatch.setattr(Checkout, 'shipping_method', shipping_method_mock)

    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    deliveries = list(checkout.deliveries)

    assert deliveries[0][1] == shipping_price
    assert deliveries[0][2] == TaxedMoney(
        net=cost_with_shipping, gross=cost_with_shipping)
    assert deliveries[0][0][0][0] == partition


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
    request = rf.get('checkout:index')
    request.user = checkout.user
    request.session = {STORAGE_SESSION_KEY: checkout.for_storage()}
    request.discounts = []
    monkeypatch.setattr(
        'saleor.cart.utils.get_cart_from_request', lambda req, qs: cart)
    response = views.index_view(request)
    assert response.status_code == status_code
    assert response.url == url


def test_checkout_discount(request_cart, sale, product_in_stock):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    checkout = Checkout(request_cart, AnonymousUser(), 'tracking_code')
    assert checkout.get_total() == TaxedMoney(
        net=Money(5, 'USD'), gross=Money(5, 'USD'))


def test_checkout_create_order_insufficient_stock(
        request_cart, customer_user, product_in_stock, billing_address,
        shipping_method):
    product_type = product_in_stock.product_type
    product_type.is_shipping_required = False
    product_type.save()
    customer_user.default_billing_address = billing_address
    customer_user.save()
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


def test_note_in_created_order(request_cart, customer_user, billing_address):
    customer_user.default_billing_address = billing_address
    checkout = Checkout(request_cart, customer_user, 'tracking_code')
    checkout.note = ''
    order = checkout.create_order()
    assert not order.notes.all()
    checkout.note = 'test_note'
    order = checkout.create_order()
    assert order.notes.values()[0].get('content') == 'test_note'
