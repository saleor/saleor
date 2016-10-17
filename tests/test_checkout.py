import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from mock import MagicMock, Mock
from prices import Price

from saleor.checkout import views
from saleor.checkout.core import STORAGE_SESSION_KEY, Checkout
from saleor.shipping.models import ShippingMethodCountry
from saleor.userprofile.models import Address


def test_checkout_version():
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    storage = checkout.for_storage()
    assert storage['version'] == Checkout.VERSION


@pytest.mark.parametrize('storage_data, expected_storage', [
    ({'version': Checkout.VERSION, 'new': 1}, {'version': Checkout.VERSION, 'new': 1}),
    ({'version': 'wrong', 'new': 1}, {'version': Checkout.VERSION}),
    ({'new': 1}, {'version': Checkout.VERSION}),
    ({}, {'version': Checkout.VERSION}),
    (None, {'version': Checkout.VERSION}),
])
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
    partition = Mock(
        get_total=Mock(return_value=Price(10, currency=settings.DEFAULT_CURRENCY)),
        get_price_per_item=Mock(return_value=Price(10, currency=settings.DEFAULT_CURRENCY)))

    def f():
        yield partition

    partition.__iter__ = Mock(return_value=f())
    cart = Mock(partition=Mock(return_value=[partition]),
                currency=settings.DEFAULT_CURRENCY)
    checkout = Checkout(
        cart, AnonymousUser(), 'tracking_code')
    deliveries = list(checkout.deliveries)
    assert deliveries[0][1] == Price(0, currency=settings.DEFAULT_CURRENCY)
    assert deliveries[0][2] == partition.get_total()
    assert deliveries[0][0][0][0] == partition


def test_checkout_deliveries_with_shipping_method(monkeypatch):
    shipping_cost = 5
    items_cost = 5

    partition = Mock(
        is_shipping_required=MagicMock(return_value=True),
        get_total=Mock(return_value=Price(items_cost, currency=settings.DEFAULT_CURRENCY)),
        get_price_per_item=Mock(return_value=Price(items_cost, currency=settings.DEFAULT_CURRENCY)))

    def f():
        yield partition

    partition.__iter__ = Mock(return_value=f())
    cart = Mock(partition=Mock(return_value=[partition]),
                currency=settings.DEFAULT_CURRENCY)

    shipping_method_mock = Mock(get_total=Mock(return_value=Price(shipping_cost, currency=settings.DEFAULT_CURRENCY)))
    monkeypatch.setattr(Checkout, 'shipping_method', shipping_method_mock)

    checkout = Checkout(
        cart, AnonymousUser(), 'tracking_code')

    deliveries = list(checkout.deliveries)
    assert deliveries[0][1] == Price(shipping_cost, currency=settings.DEFAULT_CURRENCY)
    assert deliveries[0][2] == Price(items_cost + shipping_cost, currency=settings.DEFAULT_CURRENCY)
    assert deliveries[0][0][0][0] == partition


@pytest.mark.parametrize('user, shipping', [
    (Mock(default_shipping_address='user_shipping'), 'user_shipping'),
    (AnonymousUser(), None),
])
def test_checkout_shipping_address_with_anonymous_user(user, shipping):
    checkout = Checkout(Mock(), user, 'tracking_code')
    assert checkout.shipping_address == shipping


@pytest.mark.parametrize('address_objects, shipping', [
    (Mock(get=Mock(return_value='shipping')), 'shipping'),
    (Mock(get=Mock(side_effect=Address.DoesNotExist)), None),
])
def test_checkout_shipping_address_with_storage(address_objects, shipping, monkeypatch):
    monkeypatch.setattr('saleor.checkout.core.Address.objects', address_objects)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_address'] = {'id': 1}
    assert checkout.shipping_address == shipping


def test_checkout_shipping_address_setter():
    address = Address(first_name='Jan', last_name='Kowalski')
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.shipping_address = address
    assert checkout.storage['shipping_address'] == {
        'city': u'', 'city_area': u'', 'company_name': u'', 'country': '', 'phone': u'',
        'country_area': u'', 'first_name': 'Jan', 'id': None, 'last_name': 'Kowalski',
        'postal_code': u'', 'street_address_1': u'', 'street_address_2': u''}


@pytest.mark.parametrize('shipping_address, shipping_method, value', [
    (Mock(country=Mock(code='PL')),
     Mock(country_code='PL', __eq__=lambda n, o: n.country_code == o.country_code),
     Mock(country_code='PL')),
    (Mock(country=Mock(code='DE')), Mock(country_code='PL'), None),
    (None, Mock(country_code='PL'), None),
])
def test_checkout_shipping_method(shipping_address, shipping_method, value, monkeypatch):
    queryset = Mock(get=Mock(return_value=shipping_method))
    monkeypatch.setattr(Checkout, 'shipping_address', shipping_address)
    monkeypatch.setattr('saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_method_country_id'] = 1
    assert checkout.shipping_method == value


def test_checkout_shipping_does_not_exists(monkeypatch):
    queryset = Mock(get=Mock(side_effect=ShippingMethodCountry.DoesNotExist))
    monkeypatch.setattr('saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    checkout.storage['shipping_method_country_id'] = 1
    assert checkout.shipping_method is None


def test_checkout_shipping_method_setter():
    shipping_method = Mock(id=1)
    checkout = Checkout(Mock(), AnonymousUser(), 'tracking_code')
    assert checkout.modified is False
    checkout.shipping_method = shipping_method
    assert checkout.modified is True
    assert checkout.storage['shipping_method_country_id'] == 1


@pytest.mark.parametrize('user, address', [
    (AnonymousUser(), None),
    (Mock(default_billing_address='billing_address',
          addresses=Mock(is_authenticated=Mock(return_value=True))), 'billing_address'),
])
def test_checkout_billing_address(user, address):
    checkout = Checkout(Mock(), user, 'tracking_code')
    assert checkout.billing_address == address


@pytest.mark.parametrize('cart, status_code, url', [
    (Mock(__len__=Mock(return_value=0)), 302, '/cart/'),
    (Mock(__len__=Mock(return_value=1),
          is_shipping_required=Mock(return_value=True)),
     302, '/checkout/shipping-address/'),
    (Mock(__len__=Mock(return_value=1),
          is_shipping_required=Mock(return_value=False)),
     302, '/checkout/summary/'),
    (Mock(__len__=Mock(return_value=0),
          is_shipping_required=Mock(return_value=False)), 302, '/cart/'),
])
def test_index_view(cart, status_code, url, rf):
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    request = rf.get('checkout:index')
    request.user = checkout.user
    request.session = {STORAGE_SESSION_KEY: checkout.for_storage()}
    request.discounts = []
    response = views.index_view(request, checkout, checkout.cart)
    assert response.status_code == status_code
    assert response.url == url
