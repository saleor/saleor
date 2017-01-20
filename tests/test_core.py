import pytest
from mock import Mock

from saleor.core.utils import (
    Country, get_country_by_ip, get_currency_for_country, create_superuser)
from saleor.core.utils.random_data import (create_shipping_methods,
                                           create_fake_user, create_users,
                                           create_address, create_attribute,
                                           create_product_classes_by_schema)
from saleor.shipping.models import ShippingMethod
from saleor.userprofile.models import User, Address


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
    for _ in create_shipping_methods():
        pass
    assert ShippingMethod.objects.all().count() == 2


def test_create_fake_user(db):
    assert User.objects.all().count() == 0
    create_fake_user()
    assert User.objects.all().count() == 1
    user = User.objects.all().first()
    assert not user.is_superuser


def test_create_fake_users(db):
    how_many = 5
    for _ in create_users(how_many):
        pass
    assert User.objects.all().count() == 5


def test_create_address(db):
    assert Address.objects.all().count() == 0
    create_address()
    assert Address.objects.all().count() == 1


def test_create_attribute(db):
    data = {'name': 'best_attribute', 'display': 'Best attribute'}
    attribute = create_attribute(**data)
    assert attribute.name == data['name']
    assert attribute.display == data['display']


def test_create_product_classes_by_schema(db):
    schema = {'T-Shirt': {
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
    p_class = create_product_classes_by_schema(schema)[0][0]
    assert p_class.name == 'T-Shirt'
    assert p_class.product_attributes.count() == 2
    assert p_class.variant_attributes.count() == 1
    assert p_class.is_shipping_required

