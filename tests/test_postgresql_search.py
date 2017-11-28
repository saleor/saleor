from __future__ import unicode_literals

from saleor.product.models import Product

from django.core.urlresolvers import reverse
from decimal import Decimal
import pytest


@pytest.fixture(scope='function', autouse=True)
def postgresql_search_enabled(settings):
    settings.ELASTICSEARCH_URL = None
    settings.ENABLE_SEARCH = True
    settings.PREFER_DB_SEARCH = True


@pytest.mark.integration
def test_dummy_integration(client):
    phrase = 'foo'
    client.get(reverse('search:search'), {'q': phrase})


PRODUCTS = [('Arabica Coffee', 'The best grains in galactic'),
            ('Cool T-Shirt', 'Blue and big.'),
            ('Roasted chicken', 'Fabulous vertebrate')]


@pytest.fixture
def named_products(default_category, product_class):
    products = []
    for name, description in PRODUCTS:
        product = Product.objects.create(
            name=name,
            description=description,
            price=Decimal(6.6),
            product_class=product_class)
        product.categories.add(default_category)
        products.append(product)
    return products


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_search_empty_results(admin_client, named_products):
    phrase = 'foo'
    resp = admin_client.get(reverse('dashboard:search'), {'q': phrase})
    assert 0 == len(resp.context['products'])
    assert phrase == resp.context['query']


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_find_product_by_name(admin_client, named_products):
    phrase = 'Coffee'
    resp = admin_client.get(reverse('dashboard:search'), {'q': phrase})
    assert 1 == len(resp.context['products'])
    assert named_products[0] in resp.context['products']


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_find_product_by_description(admin_client, named_products):
    phrase = 'big'
    resp = admin_client.get(reverse('dashboard:search'), {'q': phrase})
    assert 1 == len(resp.context['products'])
    assert named_products[1] in resp.context['products']
