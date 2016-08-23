from mock import Mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from prices import Price
import pytest

from .core import Checkout, STORAGE_SESSION_KEY
from ..cart import Cart
from ..shipping.models import ShippingMethodCountry
from ..userprofile.models import Address
from . import views


def fake_cart(_len, shipping_required=True):
    return Mock(
        spec=Cart,
        __len__=Mock(return_value=_len),
        is_shipping_required=Mock(return_value=shipping_required))


def test_checkout_version():
    checkout = Checkout(fake_cart(0), AnonymousUser(), 'tracking_code')
    storage = checkout.for_storage()
    assert storage['version'] == Checkout.VERSION


@pytest.mark.parametrize(
    'storage_data, expected_storage', [
        ({'version': Checkout.VERSION, 'new': 1},
         {'version': Checkout.VERSION, 'new': 1}),
        ({'version': 'wrong', 'new': 1},
         {'version': Checkout.VERSION}),
        ({'new': 1},
         {'version': Checkout.VERSION}),
        ({},
         {'version': Checkout.VERSION}),
        (None,
         {'version': Checkout.VERSION})])
def test_checkout_version_with_from_storage(storage_data, expected_storage):
    checkout = Checkout.from_storage(
        storage_data, fake_cart(0), AnonymousUser(), 'tracking_code')
    storage = checkout.for_storage()
    assert storage == expected_storage


def test_checkout_clear_storage():
    checkout = Checkout(fake_cart(0), AnonymousUser(), 'tracking_code')
    checkout.storage['new'] = 1
    checkout.clear_storage()
    assert checkout.storage is None
    assert checkout.modified is True


def test_checkout_is_shipping_required():
    cart = fake_cart(1, shipping_required=True)
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    assert checkout.is_shipping_required is True


def test_checkout_deliveries():
    partition = Mock(
        get_total=Mock(
            return_value=Price(10, currency=settings.DEFAULT_CURRENCY)))
    cart = Mock(partition=Mock(return_value=[partition]))
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    deliveries = list(checkout.deliveries)
    total = partition.get_total()
    assert deliveries == [
        (partition, Price(0, currency=settings.DEFAULT_CURRENCY), total)]


def test_checkout_deliveries_with_shipping_method(monkeypatch):
    partition = Mock(
        get_total=Mock(
            return_value=Price(10, currency=settings.DEFAULT_CURRENCY)))
    cart = Mock(partition=Mock(return_value=[partition]))
    shipping_method_mock = Mock(
        get_total=Mock(
            return_value=Price(5, currency=settings.DEFAULT_CURRENCY)))
    monkeypatch.setattr(Checkout, 'shipping_method', shipping_method_mock)
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    deliveries = list(checkout.deliveries)
    total = partition.get_total() + shipping_method_mock.get_total()
    assert deliveries == [
        (partition, shipping_method_mock.get_total(), total)]


@pytest.mark.parametrize(
    'user, shipping', [
        (Mock(default_shipping_address='user_shipping'), 'user_shipping'),
        (AnonymousUser(), None)])
def test_checkout_shipping_address_with_anonymous_user(user, shipping):
    checkout = Checkout(Mock(), user, 'tracking_code')
    assert checkout.shipping_address == shipping


@pytest.mark.parametrize(
    'address_objects, shipping', [
        (Mock(get=Mock(return_value='shipping')), 'shipping'),
        (Mock(get=Mock(side_effect=Address.DoesNotExist)), None)])
def test_checkout_shipping_address_with_storage(
        address_objects, shipping, monkeypatch):
    monkeypatch.setattr(
        'saleor.checkout.core.Address.objects', address_objects)
    checkout = Checkout(fake_cart(1), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_address'] = {'id': 1}
    assert checkout.shipping_address == shipping


def test_checkout_shipping_address_setter():
    address = Address(first_name='Jan', last_name='Kowalski')
    checkout = Checkout(fake_cart(1), AnonymousUser(), 'tracking_code')
    checkout.shipping_address = address
    assert checkout.storage['shipping_address'] == {
        'city': u'',
        'city_area': u'',
        'company_name': u'',
        'country': '',
        'country_area': u'',
        'first_name': 'Jan',
        'id': None,
        'last_name': 'Kowalski',
        'phone': u'',
        'postal_code': u'',
        'street_address_1': u'',
        'street_address_2': u''}


@pytest.mark.parametrize(
    'shipping_address, value', [
        (Mock(country=Mock(code='PL')), Mock(country_code='PL')),
        (Mock(country=Mock(code='DE')), None),
        (None, None)])
def test_checkout_shipping_method(shipping_address, value, monkeypatch):
    monkeypatch.setattr(Checkout, 'shipping_address', shipping_address)
    shipping_method = Mock(
        country_code='PL',
        __eq__=lambda n, o: n.country_code == o.country_code)
    queryset = Mock(get=Mock(return_value=shipping_method))
    monkeypatch.setattr(
        'saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    checkout = Checkout(fake_cart(1), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_method_country_id'] = 1
    assert checkout.shipping_method == value


def test_checkout_shipping_does_not_exists(monkeypatch):
    queryset = Mock(get=Mock(side_effect=ShippingMethodCountry.DoesNotExist))
    monkeypatch.setattr(
        'saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    checkout = Checkout(fake_cart(1), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_method_country_id'] = 1
    assert checkout.shipping_method is None


def test_checkout_shipping_method_setter():
    shipping_method = Mock(id=1)
    checkout = Checkout(fake_cart(1), AnonymousUser(), 'tracking_code')
    assert checkout.modified is False
    checkout.shipping_method = shipping_method
    assert checkout.modified is True
    assert checkout.storage['shipping_method_country_id'] == 1


@pytest.mark.parametrize(
    'user, address', [
        (AnonymousUser(), None),
        (Mock(default_billing_address='WATCHDOG'), 'WATCHDOG')])
def test_checkout_billing_address(user, address):
    checkout = Checkout(fake_cart(1), user, 'tracking_code')
    assert checkout.billing_address == address


@pytest.mark.parametrize(
    'cart, url', [
        (fake_cart(0), '/cart/'),
        (fake_cart(1), '/checkout/shipping-address/'),
        (fake_cart(1, shipping_required=False), '/checkout/summary/'),
        (fake_cart(0, shipping_required=False), '/cart/')])
def test_index_view(cart, url, rf):
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    request = rf.get('checkout:index')
    request.user = checkout.user
    request.cart = checkout.cart
    request.session = {STORAGE_SESSION_KEY: checkout.for_storage()}
    request.discounts = []
    response = views.index_view(request, checkout)
    assert response.status_code == 302
    assert response.url == url
