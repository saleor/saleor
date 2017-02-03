import pytest
from mock import Mock

from django.core.urlresolvers import reverse
from django.conf import settings

from saleor.core.middleware import CountryMiddleware
from saleor.core.utils import (
    Country, create_superuser, get_country_by_ip, get_currency_for_country,
    random_data)
from saleor.core.views import COOKIE_COUNTRY
from saleor.discount.models import Sale, Voucher
from saleor.order.models import Order
from saleor.product.models import Product
from saleor.shipping.models import ShippingMethod
from saleor.userprofile.models import Address, User
from .utils import get_redirect_location


class_schema = {'Vegetable': {
                   'category': 'Food',
                   'product_attributes': {
                       'Sweetness': ['Sweet', 'Sour'],
                       'Healthiness': ['Healthy', 'Not really']
                   },
                   'variant_attributes': {
                       'GMO': ['Yes', 'No']
                   },
                   'images_dir': 'candy/',
                   'is_shipping_required': True}}


@pytest.mark.parametrize('ip_data, expected_country', [
    ({'country': {'iso_code': 'PL'}}, Country('PL')),
    ({'country': {'iso_code': 'UNKNOWN'}}, None),
    (None, None),
    ({}, None),
    ({'country': {}}, None)])
def test_get_country_by_ip(ip_data, expected_country, monkeypatch):
    monkeypatch.setattr(
        'saleor.core.utils.georeader.get',
        Mock(return_value=ip_data))
    country = get_country_by_ip('127.0.0.1')
    assert country == expected_country


@pytest.mark.parametrize('country, expected_currency', [
    (Country('PL'), 'PLN'),
    (Country('US'), 'USD'),
    (Country('GB'), 'GBP')])
def test_get_currency_for_country(country, expected_currency, monkeypatch):
    currency = get_currency_for_country(country)
    assert currency == expected_currency


def test_create_superuser(db, client):
    credentials = {'email': 'admin@example.com', 'password': 'admin'}
    # Test admin creation
    assert User.objects.all().count() == 0
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    admin = User.objects.all().first()
    assert admin.is_superuser
    # Test duplicating
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    # Test logging in
    response = client.post('/account/login/',
                           {'login': credentials['email'],
                            'password': credentials['password']},
                           follow=True)
    assert response.context['request'].user == admin


def test_create_shipping_methods(db):
    assert ShippingMethod.objects.all().count() == 0
    for _ in random_data.create_shipping_methods():
        pass
    assert ShippingMethod.objects.all().count() == 2


def test_create_fake_user(db):
    assert User.objects.all().count() == 0
    random_data.create_fake_user()
    assert User.objects.all().count() == 1
    user = User.objects.all().first()
    assert not user.is_superuser


def test_create_fake_users(db):
    how_many = 5
    for _ in random_data.create_users(how_many):
        pass
    assert User.objects.all().count() == 5


def test_create_address(db):
    assert Address.objects.all().count() == 0
    random_data.create_address()
    assert Address.objects.all().count() == 1


def test_create_attribute(db):
    data = {'name': 'best_attribute', 'display': 'Best attribute'}
    attribute = random_data.create_attribute(**data)
    assert attribute.name == data['name']
    assert attribute.display == data['display']


def test_create_product_classes_by_schema(db):
    p_class = random_data.create_product_classes_by_schema(class_schema)[0][0]
    assert p_class.name == 'Vegetable'
    assert p_class.product_attributes.count() == 2
    assert p_class.variant_attributes.count() == 1
    assert p_class.is_shipping_required


def test_create_products_by_class(db):
    assert Product.objects.all().count() == 0
    how_many = 5
    p_class = random_data.create_product_classes_by_schema(class_schema)[0][0]
    random_data.create_products_by_class(p_class, class_schema['Vegetable'],
                                         '/', how_many=how_many,
                                         create_images=False)
    assert Product.objects.all().count() == how_many


def test_create_fake_order(db):
    for _ in random_data.create_shipping_methods():
        pass
    for _ in random_data.create_users(3):
        pass
        random_data.create_products_by_schema('/', 10, False)
    how_many = 5
    for _ in random_data.create_orders(how_many):
        pass
    Order.objects.all().count() == 5


def test_create_product_sales(db):
    how_many = 5
    for _ in random_data.create_product_sales(how_many):
        pass
    assert Sale.objects.all().count() == 5


def test_create_vouchers(db):
    assert Voucher.objects.all().count() == 0
    for _ in random_data.create_vouchers():
        pass
    assert Voucher.objects.all().count() == 2


@pytest.mark.parametrize('method', ['get', 'post'])
def test_set_country_no_changes(client, method):
    url = reverse('set-country')
    response_function = getattr(client, method)
    response = response_function(url, {})
    assert response.status_code == 302
    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('home')


def test_set_country_without_next(client):
    url = reverse('set-country')
    response = client.post(url, {'country': 'DK'})
    assert response.status_code == 302
    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('home')

    cookie_value = client.cookies.get(COOKIE_COUNTRY).value
    assert cookie_value == 'DK'


def test_set_country(client):
    url = reverse('set-country')
    response = client.post(url, {'country': 'PL', 'next': 'cart/'})
    assert response.status_code == 302
    redirect_location = get_redirect_location(response)
    assert redirect_location == 'cart/'

    cookie_value = client.cookies.get(COOKIE_COUNTRY).value
    assert cookie_value == 'PL'


def test_set_country_wrong_country(client):
    url = reverse('set-country')
    response = client.post(url, {'country': 'PL124', 'next': 'cart/'})
    assert response.status_code == 302
    redirect_location = get_redirect_location(response)
    assert redirect_location == 'cart/'

    cookie_value = client.cookies.get(COOKIE_COUNTRY)
    assert cookie_value is None


def test_country_middleware_with_cookie():
    country_middleware = CountryMiddleware()
    request = Mock()
    request.COOKIES = {COOKIE_COUNTRY: 'LI'}
    country_middleware.process_request(request)
    assert request.country.code == 'LI'


def test_country_middleware_without_cookie():
    country_middleware = CountryMiddleware()
    request = Mock()
    request.META = {'HTTP_X_FORWARDED_FOR': '127.0.0.1'}
    request.COOKIES = {}
    country_middleware.process_request(request)
    default_country = settings.DEFAULT_COUNTRY
    assert request.country.code == default_country
