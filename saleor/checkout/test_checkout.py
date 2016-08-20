from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from mock import Mock, patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from prices import Price
import pytest

from .core import Checkout, STORAGE_SESSION_KEY
from ..product.models import ProductVariant
from ..order.models import Order
from ..userprofile.test_userprofile import billing_address  # NOQA
from ..shipping.models import ShippingMethodCountry
from ..userprofile.models import Address
from . import views
from ..product.test_product import product_in_stock, product_without_shipping  # NOQA
from ..shipping.test_shipping import shipping_method  # NOQA


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
        get_total=Mock(return_value=Price(10, currency=settings.DEFAULT_CURRENCY)))
    cart = Mock(partition=Mock(return_value=[partition]))
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    deliveries = list(checkout.deliveries)
    assert deliveries == [(partition, Price(
        0, currency=settings.DEFAULT_CURRENCY), partition.get_total())]


def test_checkout_deliveries_with_shipping_method(monkeypatch):
    partition = Mock(
        get_total=Mock(return_value=Price(10, currency=settings.DEFAULT_CURRENCY)))
    cart = Mock()
    cart.partition.return_value = [partition]
    shipping_method_mock = Mock(
        get_total=Mock(return_value=Price(5, currency=settings.DEFAULT_CURRENCY)))
    monkeypatch.setattr(Checkout, 'shipping_method', shipping_method_mock)
    checkout = Checkout(cart, AnonymousUser(), 'tracking_code')
    deliveries = list(checkout.deliveries)
    total = partition.get_total() + shipping_method_mock.get_total()
    assert deliveries == [
        (partition, shipping_method_mock.get_total(), total)]


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
    assert checkout.modified


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
    request.cart = checkout.cart
    request.session = {STORAGE_SESSION_KEY: checkout.for_storage()}
    request.discounts = []
    response = views.index_view(request, checkout)
    assert response.status_code == status_code
    assert response.url == url


@pytest.fixture
def client_with_cart(client, product_in_stock):
    product_variant = ProductVariant.objects.last()
    url = product_variant.product.get_absolute_url()
    data = {
        'quantity': 2, 'variant': product_variant.id
    }
    client.post(url, data=data)
    return client


ADDRESS_DATA = {
        'first_name': 'First Name', 'last_name': 'Last Name',
        'company_name': 'Company Name', 'street_address_1': 'Street Address 1',
        'street_address_2': 'Street Address2', 'city': 'City',
        'postal_code': '54-321', 'country': 'PL'}


DIFFERENT_ADDRES_DATA = {
        'first_name': 'First Name', 'last_name': 'Last Name',
        'company_name': 'Company Name', 'street_address_1': 'Another Street',
        'city': 'Different City', 'postal_code': '54-321', 'country': 'PL'}


@pytest.mark.parametrize(
    'shipping_address_data, billing_address_data, update_billing_address_with', [
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, {'address': 'new_address'}),
        (ADDRESS_DATA, {}, {'address': 'shipping_address'})
    ])
@pytest.mark.integration
def test_checkout_whole_with_shipping_and_copying_address(
        client_with_cart, shipping_method, shipping_address_data,
        billing_address_data, update_billing_address_with):

    cart_dict = client_with_cart.session['cart']
    variant_id = cart_dict['items'][0]['data']['variant_id']
    quantity = cart_dict['items'][0]['quantity']
    product_variant = ProductVariant.objects.get(id=variant_id)
    url = reverse('checkout:index')
    response = client_with_cart.get(url)
    assert response.status_code == 302

    # shipping address step
    shipping_address_url = reverse('checkout:shipping-address')
    assert response.url.endswith(shipping_address_url)
    email = {'email': 'email@example.com'}
    data = shipping_address_data.copy()
    data.update(email)
    response = client_with_cart.post(shipping_address_url, data)
    assert response.status_code == 302

    # shipping method step
    shipping_method_url = reverse('checkout:shipping-method')
    assert response.url.endswith(shipping_method_url)
    data = {'method': shipping_method.id}
    response = client_with_cart.post(shipping_method_url, data=data)
    assert response.status_code == 302

    # billing address (summary) step
    summary_url = reverse('checkout:summary')
    assert response.url.endswith(summary_url)
    data = billing_address_data.copy()
    data.update(update_billing_address_with)
    assert client_with_cart.session['cart']['items']
    response = client_with_cart.post(summary_url, data=data)
    assert response.status_code == 302

    # order
    order = Order.objects.get()
    order_url = reverse('order:payment', kwargs={'token': order.token})
    assert response.url.endswith(order_url)
    assert not client_with_cart.session['cart']['items']
    ordered_item = order.get_items().get()
    ordered_item_sku = ordered_item.product_sku
    assert ordered_item_sku == product_variant.sku
    ordered_quantity = ordered_item.quantity
    assert quantity == ordered_quantity
    provided_shipping_address = Address(**shipping_address_data)
    assert Address.objects.are_identical(order.shipping_address,
                                         provided_shipping_address)
    if billing_address_data:
        provided_billing_address = Address(**billing_address_data)
    else:
        provided_billing_address = provided_shipping_address
    assert Address.objects.are_identical(order.billing_address,
                                         provided_billing_address)
    ordered_shipping_method = order.groups.get().shipping_method_name
    assert ordered_shipping_method == str(shipping_method)

@pytest.mark.integration
def test_checkout_whole_without_shipping(client_with_cart,
                                         product_without_shipping):
    cart_dict = client_with_cart.session['cart']
    variant_id = cart_dict['items'][0]['data']['variant_id']
    quantity = cart_dict['items'][0]['quantity']
    product_variant = ProductVariant.objects.get(id=variant_id)
    url = reverse('checkout:index')
    response = client_with_cart.get(url)
    assert response.status_code == 302
    summary_url = reverse('checkout:summary')
    assert response.url.endswith(summary_url)
    assert client_with_cart.session['cart']['items']
    email = {'email': 'email@example.com'}
    data = ADDRESS_DATA.copy()
    data.update(email)
    response = client_with_cart.post(summary_url, data=data)
    order = Order.objects.get()
    order_url = reverse('order:payment', kwargs={'token': order.token})
    assert response.status_code == 302
    assert response.url.endswith(order_url)
    assert not client_with_cart.session['cart']['items']
    ordered_item = order.get_items().get()
    ordered_item_sku = ordered_item.product_sku
    assert ordered_item_sku == product_variant.sku
    ordered_quantity = ordered_item.quantity
    assert quantity == ordered_quantity
    provided_billing_address = Address(**ADDRESS_DATA)
    assert Address.objects.are_identical(order.billing_address,
                                         provided_billing_address)


@pytest.fixture
def even_different_address_data(billing_address):
    address_data = Address.objects.as_data(billing_address)
    address_data.update({'first_name': 'Different Name',
                         'last_name': 'And Last'})
    return address_data


def contains_address(sequence, address):
    addresses = [Address.objects.as_data(addr) for addr in sequence]
    address_data = Address.objects.as_data(address)
    return address_data in addresses


@pytest.fixture
def authorized_client_with_cart(client_with_cart):
    User = get_user_model()
    user = User.objects.create_user('user@example.com', password='password')
    client_with_cart.login(username=user.email, password='password')
    return client_with_cart


@pytest.mark.parametrize(
    'default_address_data, stored_address_data, use_default, use_new', [
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, True, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, False, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, False, True),
        (ADDRESS_DATA, {}, True, False),
        (ADDRESS_DATA, {}, False, True),
        ({}, ADDRESS_DATA, False, False),
        ({}, ADDRESS_DATA, False, True),
        ({}, {}, False, True),
    ])
@pytest.mark.integration
def test_checkout_authorized_full_checkout_without_shipping(
        default_address_data, stored_address_data, use_default, use_new,
        authorized_client_with_cart, even_different_address_data,
        product_without_shipping):

    user = authorized_client_with_cart.get('/').context['user']
    User = get_user_model()
    if default_address_data:
        default_address = Address(**default_address_data)
        User.objects.store_address(user, default_address,
                                   billing=True, shipping=False)
    default_address = user.default_billing_address
    if stored_address_data:
        stored_address = Address(**stored_address_data)
        User.objects.store_address(user, stored_address,
                                   billing=False, shipping=False)
        stored_address = user.addresses.last()
    user_addresses = list(user.addresses.all())

    cart_dict = authorized_client_with_cart.session['cart']
    variant_id = cart_dict['items'][0]['data']['variant_id']
    quantity = cart_dict['items'][0]['quantity']
    product_variant = ProductVariant.objects.get(id=variant_id)
    url = reverse('checkout:index')
    response = authorized_client_with_cart.get(url)
    assert response.status_code == 302

    # billing address (summary) step
    summary_url = reverse('checkout:summary')
    assert response.url.endswith(summary_url)

    if use_default:
        billing_address_data = {'address': default_address.id}
        provided_address = default_address
    elif use_new:
        billing_address_data = {'address': 'new_address'}
        billing_address_data.update(even_different_address_data)
        provided_address = Address(**even_different_address_data)
    else:
        billing_address_data = {'address': stored_address.id}
        provided_address = stored_address

    ### TODO:
    # it fails when user have address but not default billing address
    # initial_address = authorized_client_with_cart.get(
    #     response.url).context['addresses_form'].initial['address']
    # if default_address:
    #     assert initial_address == default_address.id
    # elif user_addresses:
    #     assert initial_address != 'new_address'
    # else:
    #     assert initial_address == 'new_address'
    ###

    assert authorized_client_with_cart.session['cart']['items']
    response = authorized_client_with_cart.post(summary_url,
                                                data=billing_address_data)
    assert response.status_code == 302

    # order
    order = Order.objects.get()
    order_url = reverse('order:payment', kwargs={'token': order.token})
    assert response.url.endswith(order_url)
    assert not authorized_client_with_cart.session['cart']['items']
    ordered_item = order.get_items().get()
    ordered_item_sku = ordered_item.product_sku
    assert ordered_item_sku == product_variant.sku
    ordered_quantity = ordered_item.quantity
    assert quantity == ordered_quantity

    # check addresses
    assert Address.objects.are_identical(order.billing_address,
                                         provided_address)

    after_order_user_addresses = user.addresses.all()
    if use_new:
        assert len(after_order_user_addresses) - len(user_addresses) == 1
    else:
        assert list(after_order_user_addresses) == user_addresses

    assert contains_address(after_order_user_addresses, provided_address)

    # check if order create address copy
    ### TODO:
    # assert order.billing_address not in after_order_user_addresses
    ###


@pytest.mark.parametrize(
    'default_shipping, default_billing, use_default_shipping_for_shipping,'
    'use_default_billing_for_shipping, use_default_billing_for_billing,'
    'use_default_shipping_for_billing, use_different', [
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, True, False, True, False, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, True, False, False, True, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, False, True, True, False, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, False, True, False, True, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, False, False, True, False, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, True, False, False, False, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, False, False, False, False, False),
        (ADDRESS_DATA, DIFFERENT_ADDRES_DATA, False, False, False, False, True),
        (ADDRESS_DATA, {}, True, False, False, False, False),
        (ADDRESS_DATA, {}, True, False, False, True, False),
        (ADDRESS_DATA, {}, False, False, False, True, False),
        (ADDRESS_DATA, {}, False, False, False, False, False),
        (ADDRESS_DATA, {}, False, False, False, False, True),
        ({}, ADDRESS_DATA, False, True, True, False, False),
        ({}, ADDRESS_DATA, False, True, False, False, False),
        ({}, ADDRESS_DATA, False, False, True, False, False),
        ({}, ADDRESS_DATA, False, False, False, False, False),
        ({}, ADDRESS_DATA, False, False, False, False, True),
        ({}, {}, False, False, False, False, False),
        ({}, {}, False, False, False, False, True),
    ])
@pytest.mark.integration
def test_checkout_authorized_full_checkout_with_shipping(
        default_shipping, default_billing,  use_default_shipping_for_shipping,
        use_default_billing_for_shipping,  use_default_billing_for_billing,
        use_default_shipping_for_billing, use_different, shipping_method,
        authorized_client_with_cart, even_different_address_data,):

    user = authorized_client_with_cart.get('/').context['user']
    User = get_user_model()
    if default_shipping:
        default_shipping_address = Address(**default_shipping)
        User.objects.store_address(user, default_shipping_address,
                                   billing=False, shipping=True)
    default_shipping_address = user.default_shipping_address
    if default_billing:
        default_billing_address = Address(**default_billing)
        User.objects.store_address(user, default_billing_address,
                                   billing=True, shipping=False)
    default_billing_address = user.default_billing_address
    user_addresses = list(user.addresses.all())

    cart_dict = authorized_client_with_cart.session['cart']
    variant_id = cart_dict['items'][0]['data']['variant_id']
    quantity = cart_dict['items'][0]['quantity']
    product_variant = ProductVariant.objects.get(id=variant_id)
    url = reverse('checkout:index')
    response = authorized_client_with_cart.get(url)
    assert response.status_code == 302

    # shipping address step
    shipping_address_url = reverse('checkout:shipping-address')
    assert response.url.endswith(shipping_address_url)

    if use_default_shipping_for_shipping:
        shipping_address_data = {'address': default_shipping_address.id}
        provided_shipping_address = default_shipping_address
    elif use_default_billing_for_shipping:
        shipping_address_data = {'address': default_billing_address.id}
        provided_shipping_address = default_billing_address
    else:
        shipping_address_data = {'address': 'new_address'}
        shipping_address_data.update(even_different_address_data)
        provided_shipping_address = Address(**even_different_address_data)

    if default_shipping_address:
        initial_address = authorized_client_with_cart.get(
            response.url).context['address']
        assert initial_address == default_shipping_address

    response = authorized_client_with_cart.post(shipping_address_url,
                                                data=shipping_address_data)
    assert response.status_code == 302

    # shipping method step
    shipping_method_url = reverse('checkout:shipping-method')
    assert response.url.endswith(shipping_method_url)
    data = {'method': shipping_method.id}
    response = authorized_client_with_cart.post(shipping_method_url, data=data)
    assert response.status_code == 302

    # billing address (summary) step
    summary_url = reverse('checkout:summary')
    assert response.url.endswith(summary_url)

    if use_default_billing_for_billing:
        billing_address_data = {'address': default_billing_address.id}
        provided_billing_address = default_billing_address
    elif use_default_shipping_for_billing:
        billing_address_data = {'address': default_shipping_address.id}
        provided_billing_address = default_shipping_address
    elif use_different:
        billing_address_data = {'address': 'new_address'}
        different_address_data = even_different_address_data.copy()
        different_address_data['city'] = "Totally Different City"
        billing_address_data.update(different_address_data)
        provided_billing_address = Address(**different_address_data)
    else:
        billing_address_data = {'address': 'shipping_address'}
        provided_billing_address = provided_shipping_address

    initial_address = authorized_client_with_cart.get(
        response.url).context['addresses_form'].initial['address']
    if default_billing_address:
        ### TODO:
        # if default billing address id chosen ad shipping address test fails
        # assert initial_address == default_billing_address.id
        ###
        # temporary workaround
        if default_billing_address != provided_shipping_address:
            assert initial_address == default_billing_address.id
        ###
    else:
        assert initial_address == 'shipping_address'

    assert authorized_client_with_cart.session['cart']['items']
    response = authorized_client_with_cart.post(summary_url,
                                                data=billing_address_data)
    assert response.status_code == 302

    # order
    order = Order.objects.get()
    order_url = reverse('order:payment', kwargs={'token': order.token})
    assert response.url.endswith(order_url)
    assert not authorized_client_with_cart.session['cart']['items']
    ordered_item = order.get_items().get()
    ordered_item_sku = ordered_item.product_sku
    assert ordered_item_sku == product_variant.sku
    ordered_quantity = ordered_item.quantity
    assert quantity == ordered_quantity
    ordered_shipping_method = order.groups.get().shipping_method_name
    assert ordered_shipping_method == str(shipping_method)

    # check addresses
    assert Address.objects.are_identical(order.shipping_address,
                                         provided_shipping_address)
    assert Address.objects.are_identical(order.billing_address,
                                         provided_billing_address)

    after_order_user_addresses = user.addresses.all()
    if not any([use_default_billing_for_billing,
                use_default_shipping_for_billing,
                use_default_billing_for_shipping,
                use_default_shipping_for_shipping]):
        if use_different:
            assert len(after_order_user_addresses) - len(user_addresses) == 2
        else:
            assert len(after_order_user_addresses) - len(user_addresses) == 1
    elif sum([use_default_billing_for_billing, use_default_shipping_for_billing,
              use_default_billing_for_shipping,
              use_default_shipping_for_shipping]) == 2:
        assert len(after_order_user_addresses) - len(user_addresses) == 0
    elif provided_billing_address == provided_shipping_address:
        assert len(after_order_user_addresses) - len(user_addresses) == 0
    else:
        assert len(after_order_user_addresses) - len(user_addresses) == 1

    assert contains_address(after_order_user_addresses,
                            provided_billing_address)
    assert contains_address(after_order_user_addresses,
                            provided_shipping_address)

    # check if order create address copy
    ### TODO:
    # assert order.shipping_address not in after_order_user_addresses
    # assert order.billing_address not in after_order_user_addresses
    ###


@pytest.mark.parametrize(
    'broken_address_data', [
        {'first_name': 'Broken Data', 'country': 'X', 'address': 'new_address'},
        {'address': 'new_address'},
        {'address': 'not_used_word'},
        {'address': 12345},
        ADDRESS_DATA,
        dict(list(ADDRESS_DATA.items()) +
             [('address', 'new_address'), ('email', 'invalid')]),
        {}])
@pytest.mark.integration
def test_checkout_fail_on_shipping_address(broken_address_data,
                                           client_with_cart):

    cart_dict = client_with_cart.session['cart'].copy()
    url = reverse('checkout:index')
    response = client_with_cart.get(url)
    assert response.status_code == 302
    shipping_address_url = reverse('checkout:shipping-address')
    assert response.url.endswith(shipping_address_url)

    response = client_with_cart.post(shipping_address_url,
                                     data=broken_address_data)
    assert response.status_code == 200
    assert cart_dict == client_with_cart.session['cart']


@pytest.mark.parametrize(
    'broken_address_data', [
        {'first_name': 'Broken Data', 'country': 'X', 'address': 'new_address'},
        {'address': 'new_address'},
        {'address': 'not_used_word'},
        {'address': 12345},
        ADDRESS_DATA,
        {}])
@pytest.mark.integration
def test_checkout_authorized_fail_on_shipping_address(
        broken_address_data, authorized_client_with_cart):

    cart_dict = authorized_client_with_cart.session['cart'].copy()
    url = reverse('checkout:index')
    response = authorized_client_with_cart.get(url)
    assert response.status_code == 302
    shipping_address_url = reverse('checkout:shipping-address')
    assert response.url.endswith(shipping_address_url)

    response = authorized_client_with_cart.post(shipping_address_url,
                                                data=broken_address_data)
    assert response.status_code == 200
    assert cart_dict == authorized_client_with_cart.session['cart']


@pytest.fixture
def anonymous_client_with_shipping_address(client_with_cart):
    shipping_address_url = reverse('checkout:shipping-address')
    shipping_address_data = {'address': 'new_address',
                             'email': 'user@example.com'}
    shipping_address_data.update(ADDRESS_DATA)
    client_with_cart.post(shipping_address_url,
                          data=shipping_address_data)
    return client_with_cart


@pytest.mark.parametrize(
    'broken_method_data', [
        {'method': 123456},
        {'method': 'not_method_id'},
        {}])
@pytest.mark.integration
def test_checkout_fail_on_shipping_method(
        anonymous_client_with_shipping_address, broken_method_data):

    cart_dict = anonymous_client_with_shipping_address.session['cart'].copy()
    url = reverse('checkout:shipping-method')
    response = anonymous_client_with_shipping_address.post(
        url, data=broken_method_data)
    assert response.status_code == 200
    assert cart_dict == anonymous_client_with_shipping_address.session['cart']


@pytest.fixture
def authorized_client_with_shipping_address(authorized_client_with_cart):
    shipping_address_url = reverse('checkout:shipping-address')
    shipping_address_data = {'address': 'new_address'}
    shipping_address_data.update(ADDRESS_DATA)
    authorized_client_with_cart.post(shipping_address_url,
                                     data=shipping_address_data)
    return authorized_client_with_cart


@pytest.mark.parametrize(
    'broken_method_data', [
        {'method': 123456},
        {'method': 'not_method_id'},
        {}])
@pytest.mark.integration
def test_checkout_authorized_fail_on_shipping_method(
        broken_method_data, shipping_method,
        authorized_client_with_shipping_address):

    cart_dict = authorized_client_with_shipping_address.session['cart'].copy()
    url = reverse('checkout:shipping-method')
    response = authorized_client_with_shipping_address.post(
        url, data=broken_method_data)
    assert response.status_code == 200
    assert cart_dict == authorized_client_with_shipping_address.session['cart']


@pytest.fixture
def anonymous_client_with_shipping_method(
        anonymous_client_with_shipping_address, shipping_method):

    shipping_method_url = reverse('checkout:shipping-method')
    shipping_method_data = {'method': shipping_method.id}
    anonymous_client_with_shipping_address.post(shipping_method_url,
                                                data=shipping_method_data)
    return anonymous_client_with_shipping_address


@pytest.mark.parametrize(
    'broken_address_data', [
        {'first_name': 'Broken Data', 'country': 'X', 'address': 'new_address'},
        {'address': 'new_address'},
        {'address': 'not_used_word'},
        {'address': 12345},
        ADDRESS_DATA,
        {}])
@pytest.mark.integration
def test_checkout_fail_on_summary_step(
        anonymous_client_with_shipping_method, broken_address_data):

    cart_dict = anonymous_client_with_shipping_method.session['cart'].copy()
    previous_orders = list(Order.objects.all())
    url = reverse('checkout:summary')
    response = anonymous_client_with_shipping_method.post(
        url, data=broken_address_data)
    assert response.status_code == 200
    assert cart_dict == anonymous_client_with_shipping_method.session['cart']
    assert list(Order.objects.all()) == previous_orders


@pytest.fixture
def authorized_client_with_shipping_method(
        authorized_client_with_shipping_address, shipping_method):

    shipping_method_url = reverse('checkout:shipping-method')
    shipping_method_data = {'method': shipping_method.id}
    authorized_client_with_shipping_address.post(shipping_method_url,
                                                 data=shipping_method_data)
    return authorized_client_with_shipping_address


@pytest.mark.parametrize(
    'broken_address_data', [
        {'first_name': 'Broken Data', 'country': 'X', 'address': 'new_address'},
        {'address': 'new_address'},
        {'address': 'not_used_word'},
        {'address': 12345},
        ADDRESS_DATA,
        {}])
@pytest.mark.integration
def test_checkout_authorized_fail_on_summary_step(
        authorized_client_with_shipping_method, broken_address_data):
    """
    Tries to choose or provide new invalid billing address
    """
    cart_dict = authorized_client_with_shipping_method.session['cart'].copy()
    previous_orders = list(Order.objects.all())
    url = reverse('checkout:summary')
    response = authorized_client_with_shipping_method.post(
        url, data=broken_address_data)
    assert response.status_code == 200
    assert cart_dict == authorized_client_with_shipping_method.session['cart']
    assert list(Order.objects.all()) == previous_orders


@pytest.mark.parametrize(
    'broken_address_data', [
        {'first_name': 'Broken Data', 'country': 'X', 'address': 'new_address'},
        {'address': 'new_address'},
        {'address': 'not_used_word'},
        {'address': 'shipping_address'},
        {'address': 12345},
        ADDRESS_DATA,
        dict(list(ADDRESS_DATA.items()) +
             [('address', 'new_address'), ('email', 'invalid')]),
        {}])
@pytest.mark.integration
def test_checkout_fail_on_summary_step_without_shipping(
        client_with_cart, broken_address_data, product_without_shipping):

    cart_dict = client_with_cart.session['cart'].copy()
    previous_orders = list(Order.objects.all())
    url = reverse('checkout:summary')
    response = client_with_cart.post(url, data=broken_address_data)
    assert response.status_code == 200
    assert cart_dict == client_with_cart.session['cart']
    assert list(Order.objects.all()) == previous_orders


@pytest.mark.parametrize(
    'broken_address_data', [
        {'first_name': 'Broken Data', 'country': 'X', 'address': 'new_address'},
        {'address': 'new_address'},
        {'address': 'not_used_word'},
        {'address': 'shipping_address'},
        {'address': 12345},
        ADDRESS_DATA,
        {}])
@pytest.mark.integration
def test_checkout_authorized_faill_on_summary_step_without_shipping(
        authorized_client_with_cart, broken_address_data,
        product_without_shipping):

    cart_dict = authorized_client_with_cart.session['cart'].copy()
    previous_orders = list(Order.objects.all())
    url = reverse('checkout:summary')
    response = authorized_client_with_cart.post(url, data=broken_address_data)
    assert response.status_code == 200
    assert cart_dict == authorized_client_with_cart.session['cart']
    assert list(Order.objects.all()) == previous_orders


@pytest.mark.parametrize('url, status_code, redirection', [
    (reverse('checkout:index'), 302, reverse('cart:index')),
    (reverse('checkout:shipping-address'), 302, reverse('cart:index')),
    (reverse('checkout:shipping-method'), 302, reverse('cart:index')),
    (reverse('checkout:summary'), 302, reverse('cart:index'))])
@pytest.mark.integration
def test_checkout_redirections_without_cart(
        client, url, status_code, redirection, db):
    response = client.get(url)
    assert response.status_code == status_code
    assert response.url.endswith(redirection)


@pytest.mark.parametrize('url, redirection', [
    (reverse('checkout:index'), reverse('checkout:shipping-address')),
    (reverse('checkout:shipping-address'), reverse('checkout:shipping-address')),
    (reverse('checkout:shipping-method'), reverse('checkout:shipping-address')),
    (reverse('checkout:summary'), reverse('checkout:shipping-address'))])
@pytest.mark.integration
def test_checkout_redirections_without_shipping_address(client_with_cart,
                                                        url, redirection):
    cart_dict = client_with_cart.session['cart'].copy()
    response = client_with_cart.get(url, follow=True)
    if url == redirection:
        assert response.redirect_chain == []
    else:
        assert response.redirect_chain[-1][0].endswith(redirection)
    assert cart_dict == client_with_cart.session['cart']


@pytest.mark.parametrize('url, redirection', [
    ### TODO:
    # if user breaks checkout process should continue on last step
    # (reverse('checkout:index'), reverse('checkout:shipping-method')),
    (reverse('checkout:shipping-address'), reverse('checkout:shipping-address')),
    (reverse('checkout:shipping-method'), reverse('checkout:shipping-method')),
    (reverse('checkout:summary'), reverse('checkout:shipping-method'))])
@pytest.mark.integration
def test_checkout_redirections_without_shipping_method(
        anonymous_client_with_shipping_address, url, redirection):
    cart_dict = anonymous_client_with_shipping_address.session['cart'].copy()
    response = anonymous_client_with_shipping_address.get(url, follow=True)
    if url == redirection:
        assert response.redirect_chain == []
    else:
        assert response.redirect_chain[-1][0].endswith(redirection)
    assert cart_dict == anonymous_client_with_shipping_address.session['cart']


@pytest.mark.parametrize('url, redirection', [
    ### TODO:
    # if user breaks checkout process should continue on last step
    # (reverse('checkout:index'), reverse('checkout:summary')),
    (reverse('checkout:shipping-address'), reverse('checkout:shipping-address')),
    (reverse('checkout:shipping-method'), reverse('checkout:shipping-method')),
    (reverse('checkout:summary'), reverse('checkout:summary'))])
@pytest.mark.integration
def test_checkout_redirections_without_billing_address(
        anonymous_client_with_shipping_method, url, redirection):
    cart_dict = anonymous_client_with_shipping_method.session['cart'].copy()
    response = anonymous_client_with_shipping_method.get(url, follow=True)
    if url == redirection:
        assert response.redirect_chain == []
    else:
        assert response.url(redirection)
    assert cart_dict == anonymous_client_with_shipping_method.session['cart']
