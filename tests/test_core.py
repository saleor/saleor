import io
from contextlib import redirect_stdout
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import pytest
from django.shortcuts import reverse
from django.templatetags.static import static
from django.test import override_settings
from django.urls import translate_url
from measurement.measures import Weight
from prices import Money

from saleor.account.models import Address, User
from saleor.core.storages import S3MediaStorage
from saleor.core.utils import (
    Country, build_absolute_uri, create_superuser, create_thumbnails,
    format_money, get_country_by_ip, get_currency_for_country, random_data)
from saleor.core.utils.text import get_cleaner, strip_html
from saleor.core.weight import WeightUnits, convert_weight
from saleor.discount.models import Sale, Voucher
from saleor.order.models import Order
from saleor.product.models import ProductImage
from saleor.shipping.models import ShippingZone

type_schema = {
    'Vegetable': {
        'category': {
            'name': 'Food',
            'image_name': 'books.jpg'},
        'product_attributes': {
            'Sweetness': ['Sweet', 'Sour'],
            'Healthiness': ['Healthy', 'Not really']},
        'variant_attributes': {
            'GMO': ['Yes', 'No']},
        'images_dir': 'candy/',
        'is_shipping_required': True}}


def test_format_money():
    money = Money('123.99', 'USD')
    assert format_money(money) == '$123.99'


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


def test_create_superuser(db, client, media_root):
    credentials = {'email': 'admin@example.com', 'password': 'admin'}
    # Test admin creation
    assert User.objects.all().count() == 0
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    admin = User.objects.all().first()
    assert admin.is_superuser
    assert admin.avatar
    # Test duplicating
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    # Test logging in
    response = client.post(reverse('account:login'),
                           {'username': credentials['email'],
                            'password': credentials['password']},
                           follow=True)
    assert response.context['request'].user == admin


def test_create_shipping_zones(db):
    assert ShippingZone.objects.all().count() == 0
    for _ in random_data.create_shipping_zones():
        pass
    assert ShippingZone.objects.all().count() == 5


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


def test_create_fake_order(db, monkeypatch, image, media_root):
    # Tests shouldn't depend on images present in placeholder folder
    monkeypatch.setattr(
        'saleor.core.utils.random_data.get_image',
        Mock(return_value=image))
    for _ in random_data.create_shipping_zones():
        pass
    for _ in random_data.create_users(3):
        random_data.create_products_by_schema('/', 10)
    how_many = 5
    for _ in random_data.create_orders(how_many):
        pass
    assert Order.objects.all().count() == 5


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


def test_manifest(client, site_settings):
    response = client.get(reverse('manifest'))
    assert response.status_code == 200
    content = response.json()
    assert content['name'] == site_settings.site.name
    assert content['short_name'] == site_settings.site.name
    assert content['description'] == site_settings.description


def test_utils_get_cleaner_invalid_parameters():
    with pytest.raises(ValueError):
        get_cleaner(bad=True)


def test_utils_strip_html():
    base_text = ('<p>Hello</p>'
                 '\n\n'
                 '\t<b>World</b>')
    text = strip_html(base_text, strip_whitespace=True)
    assert text == 'Hello World'


@override_settings(
    VERSATILEIMAGEFIELD_SETTINGS={'create_images_on_demand': False})
def test_create_thumbnails(product_with_image, settings):
    sizeset = settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS['products']
    product_image = product_with_image.images.first()

    # There's no way to list images created by versatile prewarmer
    # So we delete all created thumbnails/crops and count them
    log_deleted_images = io.StringIO()
    with redirect_stdout(log_deleted_images):
        product_image.image.delete_all_created_images()
    log_deleted_images = log_deleted_images.getvalue()
    # Image didn't have any thumbnails/crops created, so there's no log
    assert not log_deleted_images

    create_thumbnails(product_image.pk, ProductImage, 'products')
    log_deleted_images = io.StringIO()
    with redirect_stdout(log_deleted_images):
        product_image.image.delete_all_created_images()
    log_deleted_images = log_deleted_images.getvalue()

    for image_name, method_size in sizeset:
        method, size = method_size.split('__')
        if method == 'crop':
            assert product_image.image.crop[size].name in log_deleted_images
        elif method == 'thumbnail':
            assert product_image.image.thumbnail[size].name in log_deleted_images  # noqa


@patch('storages.backends.s3boto3.S3Boto3Storage')
def test_storages_set_s3_bucket_domain(storage, settings):
    settings.AWS_MEDIA_BUCKET_NAME = 'media-bucket'
    settings.AWS_MEDIA_CUSTOM_DOMAIN = 'media-bucket.example.org'
    storage = S3MediaStorage()
    assert storage.bucket_name == 'media-bucket'
    assert storage.custom_domain == 'media-bucket.example.org'


@patch('storages.backends.s3boto3.S3Boto3Storage')
def test_storages_not_setting_s3_bucket_domain(storage, settings):
    settings.AWS_MEDIA_BUCKET_NAME = 'media-bucket'
    settings.AWS_MEDIA_CUSTOM_DOMAIN = None
    storage = S3MediaStorage()
    assert storage.bucket_name == 'media-bucket'
    assert storage.custom_domain is None


def test_set_language_redirects_to_current_endpoint(client):
    user_language_point = 'en'
    new_user_language = 'fr'
    new_user_language_point = '/fr/'
    test_endpoint = 'checkout:index'

    # get a English translated url (.../en/...)
    # and the expected url after we change it
    current_url = reverse(test_endpoint)
    expected_url = translate_url(current_url, new_user_language)

    # check the received urls:
    #   - current url is english (/en/) (default from tests.settings);
    #   - expected url is french (/fr/)
    assert user_language_point in current_url
    assert user_language_point not in expected_url
    assert new_user_language_point in expected_url

    # ensure we are getting directed to english page, not anything else
    response = client.get(reverse(test_endpoint), follow=True)
    new_url = response.request['PATH_INFO']
    assert new_url == current_url

    # change the user language to French,
    # and tell the view we want to be redirected to our current page
    set_language_url = reverse('set_language')
    data = {'language': new_user_language, 'next': current_url}

    redirect_response = client.post(set_language_url, data, follow=True)
    new_url = redirect_response.request['PATH_INFO']

    # check if we got redirected somewhere else
    assert new_url != current_url

    # now check if we got redirect the endpoint we wanted to go back
    # in the new language (checkout:index)
    assert expected_url == new_url


def test_convert_weight():
    weight = Weight(kg=1)
    expected_result = Weight(g=1000)
    assert convert_weight(weight, WeightUnits.GRAM) == expected_result


def test_build_absolute_uri(site_settings, settings):
    # Case when we are using external service for storing static files,
    # eg. Amazon s3
    url = 'https://example.com/static/images/image.jpg'
    assert build_absolute_uri(location=url) == url

    # Case when static url is resolved to relative url
    logo_url = build_absolute_uri(static('images/logo-light.svg'))
    protocol = 'https' if settings.ENABLE_SSL else 'http'
    current_url = '%s://%s' % (protocol, site_settings.site.domain)
    logo_location = urljoin(current_url, static('images/logo-light.svg'))
    assert logo_url == logo_location
