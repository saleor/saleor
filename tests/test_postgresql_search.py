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


PRODUCTS = [('Arabica Coffee', 'The best grains in galactic'),
            ('Cool T-Shirt', 'Blue and big.'),
            ('Roasted chicken', 'Fabulous vertebrate')]


@pytest.fixture
def named_products(default_category, product_class):
    def gen_product(name, description):
        product = Product.objects.create(
            name=name,
            description=description,
            price=Decimal(6.6),
            product_class=product_class)
        product.categories.add(default_category)
        return product
    return [gen_product(name, desc) for name, desc in PRODUCTS]


def search_storefront(client, phrase):
    resp = client.get(reverse('search:search'), {'q': phrase})
    return [prod for prod, _ in resp.context['results'].object_list]


@pytest.mark.parametrize('phrase,product_num',
                         [('Arabika', 0), ('Aarabica', 0), ('Arab', 0),
                          ('czicken', 2), ('blue', 1), ('roast', 2),
                          ('coool', 1)])
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_storefront_product_fuzzy_search(client, named_products, phrase,
                                         product_num):
    results = search_storefront(client, phrase)
    assert 1 == len(results)
    assert named_products[product_num] in results


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_storefront_filter_published_products(client, named_products):
    prod_to_unpublish = named_products[0]
    prod_to_unpublish.is_published = False
    prod_to_unpublish.save()
    assert search_storefront(client, 'Coffee') == []


def search_dashboard(client, phrase):
    response = client.get(reverse('dashboard:search'), {'q': phrase})
    assert phrase == response.context['query']
    context = response.context
    return context['products'], context['orders'], context['users']


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_search_empty_results(admin_client, named_products):
    products, _, _ = search_dashboard(admin_client, 'foo')
    assert 0 == len(products)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_find_product_by_name(admin_client, named_products):
    products, _, _ = search_dashboard(admin_client, 'coffee')
    assert 1 == len(products)
    assert named_products[0] in products


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_find_product_by_description(admin_client, named_products):
    products, _, _ = search_dashboard(admin_client, 'BIG')
    assert 1 == len(products)
    assert named_products[1] in products
