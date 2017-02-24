import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.forms import model_to_dict
from mock import Mock
from prices import Price

from saleor.cart.models import Cart
from saleor.checkout import views
from saleor.checkout.core import STORAGE_SESSION_KEY, Checkout
from saleor.shipping.models import ShippingMethodCountry
from saleor.userprofile.models import Address


@pytest.fixture
def anonymous_checkout():
    return Checkout(Mock(spec=Cart, discounts=None), AnonymousUser(), 'tracking_code')


@pytest.fixture
def shipping_method_factory(monkeypatch):
    def generate_shipping_method(shipping_cost):
        shipping_method_mock = Mock(spec=['get_total'],
                                    get_total=lambda: Price(shipping_cost,
                                                            currency=settings.DEFAULT_CURRENCY))
        monkeypatch.setattr(Checkout, 'shipping_method', shipping_method_mock)

    return generate_shipping_method


def test_checkout_version(anonymous_checkout):
    storage = anonymous_checkout.for_storage()
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


def test_checkout_clear_storage(anonymous_checkout):
    anonymous_checkout.storage['new'] = 1
    anonymous_checkout.clear_storage()
    assert anonymous_checkout.storage is None
    assert anonymous_checkout.modified is True


def test_checkout_is_shipping_required(anonymous_checkout):
    anonymous_checkout.cart = Mock(is_shipping_required=Mock(return_value=True))
    assert anonymous_checkout.is_shipping_required is True


def test_checkout_deliveries(anonymous_checkout, cart_with_partition_factory):
    anonymous_checkout.cart = cart_with_partition_factory(items=[{'cost': 10}])
    partition = anonymous_checkout.cart.partition()
    deliveries = list(anonymous_checkout.deliveries)
    assert deliveries[0][1] == Price(0, currency=settings.DEFAULT_CURRENCY)
    assert deliveries[0][2] == partition.get_total()
    assert deliveries[0][0][0][0] == partition.subject[0]


def test_checkout_deliveries_with_shipping_method(anonymous_checkout, cart_with_partition_factory,
                                                  shipping_method_factory):
    shipping_cost = 5
    items_cost = 5

    anonymous_checkout.cart = cart_with_partition_factory(items=[{'cost': items_cost}])
    partition = anonymous_checkout.cart.partition()
    shipping_method_factory(shipping_cost=shipping_cost)

    deliveries = list(anonymous_checkout.deliveries)
    assert deliveries[0][1] == Price(shipping_cost, currency=settings.DEFAULT_CURRENCY)
    assert deliveries[0][2] == Price(items_cost + shipping_cost, currency=settings.DEFAULT_CURRENCY)
    assert deliveries[0][0][0][0] == partition.subject[0]


@pytest.mark.parametrize('user, shipping', [
    (Mock(default_shipping_address='user_shipping'), 'user_shipping'),
    (AnonymousUser(), None),
])
def test_checkout_shipping_address_with_anonymous_user(user, shipping):
    checkout = Checkout(Mock(), user, 'tracking_code')
    assert checkout._shipping_address is None
    assert checkout.shipping_address == shipping
    assert checkout._shipping_address == shipping


@pytest.mark.parametrize('address_objects, shipping', [
    (Mock(get=Mock(return_value='shipping')), 'shipping'),
    (Mock(get=Mock(side_effect=Address.DoesNotExist)), None),
])
def test_checkout_shipping_address_with_storage(address_objects, shipping,
                                                monkeypatch, anonymous_checkout):
    monkeypatch.setattr('saleor.checkout.core.Address.objects', address_objects)
    anonymous_checkout.storage['shipping_address'] = {'id': 1}
    assert anonymous_checkout.shipping_address == shipping


def test_checkout_shipping_address_setter(anonymous_checkout, billing_address):
    assert anonymous_checkout._shipping_address is None
    anonymous_checkout.shipping_address = billing_address
    assert anonymous_checkout._shipping_address == billing_address
    for key in anonymous_checkout.storage['shipping_address'].keys():
        assert  anonymous_checkout.storage['shipping_address'][key] == getattr(billing_address, key)


@pytest.mark.parametrize('shipping_address, shipping_method, value', [
    (Mock(country=Mock(code='PL')),
     Mock(country_code='PL', __eq__=lambda n, o: n.country_code == o.country_code),
     Mock(country_code='PL')),
    (Mock(country=Mock(code='DE')), Mock(country_code='PL'), None),
    (None, Mock(country_code='PL'), None),
])
def test_checkout_shipping_method(shipping_address, shipping_method,
                                  value, monkeypatch, anonymous_checkout):
    queryset = Mock(get=Mock(return_value=shipping_method))
    monkeypatch.setattr(Checkout, 'shipping_address', shipping_address)
    monkeypatch.setattr('saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    anonymous_checkout.storage['shipping_method_country_id'] = 1
    assert anonymous_checkout._shipping_method is None
    assert anonymous_checkout.shipping_method == value
    assert anonymous_checkout._shipping_method == value


def test_checkout_shipping_does_not_exists(monkeypatch, anonymous_checkout):
    queryset = Mock(get=Mock(side_effect=ShippingMethodCountry.DoesNotExist))
    monkeypatch.setattr('saleor.checkout.core.ShippingMethodCountry.objects', queryset)
    anonymous_checkout.storage['shipping_method_country_id'] = 1
    assert anonymous_checkout.shipping_method is None


def test_checkout_shipping_method_setter(anonymous_checkout):
    shipping_method = Mock(id=1)
    assert anonymous_checkout.modified is False
    assert anonymous_checkout._shipping_method is None
    assert anonymous_checkout.modified is False
    anonymous_checkout.shipping_method = shipping_method
    assert anonymous_checkout._shipping_method == shipping_method
    assert anonymous_checkout.modified is True
    assert anonymous_checkout.storage['shipping_method_country_id'] == 1


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
def test_index_view(cart, status_code, url, rf, monkeypatch):
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    request = rf.get('checkout:index')
    request.user = checkout.user
    request.session = {STORAGE_SESSION_KEY: checkout.for_storage()}
    request.discounts = []
    monkeypatch.setattr('saleor.cart.utils.get_cart_from_request',
                        lambda req, qs : cart)
    response = views.index_view(request)
    assert response.status_code == status_code
    assert response.url == url


def test_checkout_discount(request_cart, sale, product_in_stock):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    checkout = Checkout(request_cart, AnonymousUser(), 'tracking_code')
    assert checkout.get_total() == Price(currency="USD", net=5)


def test_address_shipping_is_same_as_billing(anonymous_checkout, billing_address):
    """Pass the same address twice and check method is_shipping_same_as_billing """
    anonymous_checkout.shipping_address = billing_address
    anonymous_checkout.billing_address = billing_address

    assert anonymous_checkout.is_shipping_same_as_billing


def test_address_shipping_isnt_same_as_billing(anonymous_checkout, billing_address):
    """Pass two different addresses and check method is_shipping_same_as_billing """
    anonymous_checkout.billing_address = billing_address
    shipping_address = billing_address
    shipping_address.id = None
    shipping_address.city = 'Warszawa'
    shipping_address.save()
    anonymous_checkout.shipping_address = shipping_address
    assert not anonymous_checkout.is_shipping_same_as_billing


def test_set_shipping_address(anonymous_checkout, billing_address):
    """Set shipping address and check if checkout object is modified """
    assert anonymous_checkout.modified is False
    anonymous_checkout.shipping_address = billing_address
    assert anonymous_checkout.modified is True
    assert anonymous_checkout.storage['shipping_address'] == model_to_dict(billing_address)


def test_set_billing_address(anonymous_checkout, billing_address):
    """Set billing address and check if checkout object is modified """
    assert anonymous_checkout.modified is False
    anonymous_checkout.billing_address = billing_address
    assert anonymous_checkout.modified is True
    assert anonymous_checkout.storage['billing_address'] == model_to_dict(billing_address)


def test_set_email_address(anonymous_checkout):
    """Set email address and check if checkout object is modified """
    assert anonymous_checkout.modified is False
    anonymous_checkout.email = 'test@example.com'
    assert anonymous_checkout.modified is True
    assert anonymous_checkout.storage['email'] == 'test@example.com'


@pytest.mark.parametrize('items, subtotal', [
    ([{'cost': 10}, {'cost': 20, 'is_shipping_required': False}], 30),
    ([{'cost': 10}], 10),
])
def test_get_subtotal(anonymous_checkout, cart_with_partition_factory, items, subtotal):
    """Test checkout subtotal cost calculation for cart with multiple groups """
    anonymous_checkout.cart = cart_with_partition_factory(items=items)
    assert anonymous_checkout.get_subtotal() == Price(subtotal, currency=settings.DEFAULT_CURRENCY)


@pytest.mark.parametrize('items, total', [
    ([{'cost': 10}, {'cost': 20, 'is_shipping_required': False}], 30),
    ([{'cost': 10}], 10),
])
def test_get_total(anonymous_checkout, cart_with_partition_factory, items, total):
    """Test checkout total cost calculation for cart with multiple groups """
    anonymous_checkout.cart = cart_with_partition_factory(items=items)
    assert anonymous_checkout.get_total() == Price(total, currency=settings.DEFAULT_CURRENCY)


@pytest.mark.parametrize('items, total_shipping', [
    ([{'cost': 10}, {'cost': 20, 'is_shipping_required': False}], 5),
    ([{'cost': 10}], 5),
])
def test_get_total_shipping(anonymous_checkout, cart_with_partition_factory,
                            shipping_method_factory, items, total_shipping):
    """Test checkout total cost calculation for cart with multiple groups and shipping cost """
    shipping_method_factory(shipping_cost=5)
    anonymous_checkout.cart = cart_with_partition_factory(items=items)
    assert anonymous_checkout.get_total_shipping() == Price(total_shipping,
                                                            currency=settings.DEFAULT_CURRENCY)
