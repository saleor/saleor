from saleor.product.models import Product
from django.core.urlresolvers import reverse
from decimal import Decimal
import pytest


MATCH_SEARCH_REQUEST = ['method', 'host', 'port', 'path', 'body']
PRODUCTS_INDEXED = {15, 56}  # same as in recorded data!


@pytest.fixture(scope='function', autouse=True)
def es_autosync_disabled(settings):
    settings.ELASTICSEARCH_DSL_AUTO_REFRESH = False
    settings.ELASTICSEARCH_DSL_AUTOSYNC = False


@pytest.mark.vcr()
@pytest.fixture
def indexed_products(product_class, default_category):
    ''' Products to be found by search backend

    We need existing objects with primary keys same as search service
    returned in response. Otherwise search view won't find anything.
    Purpose of this fixture is for integration with search service only!
    pks must be in response in appropiate recorded cassette.
    '''
    def gen_product_with_id(object_id):
        product = Product.objects.create(
            pk=object_id,
            name='Test product ' + str(object_id),
            price=Decimal(10.0),
            product_class=product_class)
        product.categories.add(default_category)
        return product
    return [gen_product_with_id(prod) for prod in PRODUCTS_INDEXED]


def execute_search(client, phrase):
    response = client.get(reverse('search:search'), {'q': phrase})
    assert phrase == response.context['query']
    found_objs = response.context['results'].object_list
    return [prod.pk for prod, _ in found_objs]


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_empty_results(db, client):
    ''' no products found with foo '''
    assert 0 == len(execute_search(client, 'foo'))


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_result(db, indexed_products, client):
    ''' some products founds, only those both in search result and objects '''
    found_products = execute_search(client, 'Group')
    assert PRODUCTS_INDEXED == set(found_products)


PRODUCTS_TO_UNPUBLISH = {56}


@pytest.fixture
def products_with_mixed_publishing(indexed_products):
    products_to_unpublish = Product.objects.filter(pk__in=PRODUCTS_TO_UNPUBLISH)
    for prod in products_to_unpublish:
        prod.is_published = False
        prod.save()
    return indexed_products


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_doesnt_show_unpublished(db, products_with_mixed_publishing,
                                            client):
    published_products = PRODUCTS_INDEXED - PRODUCTS_TO_UNPUBLISH
    found_products = execute_search(client, 'Group')
    assert published_products == set(found_products)
