from __future__ import unicode_literals

from saleor.product.models import Product
from django.core.urlresolvers import reverse

from decimal import Decimal
import pytest

MATCH_SEARCH_REQUEST = ['method', 'host', 'port', 'path', 'body']
NEW_BACKEND_FOUND = {15, 34, 58}  # same as in recorded data!
PRODUCTS_INDEXED = NEW_BACKEND_FOUND

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


def _extract_pks(object_list):
    return [prod.pk for prod, _ in object_list]


@pytest.fixture
def new_search_backend():
    import saleor.search.forms
    old_backend = saleor.search.forms.USE_BACKEND
    saleor.search.forms.USE_BACKEND = 'newelastic'
    yield new_search_backend
    saleor.search.forms.USE_BACKEND = old_backend


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_empty_results(db, client, new_search_backend):
    ''' no products found with foo '''
    WORD = 'foo'
    response = client.get(reverse('search:search'), {'q': WORD})
    assert 0 == len(response.context['results'].object_list)
    assert WORD == response.context['query']


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_result(db, indexed_products, client,
                                new_search_backend):
    ''' some products founds, only those both in search result and objects '''
    EXISTING_PHRASE = 'Group'
    response = client.get(reverse('search:search'), {'q': EXISTING_PHRASE})
    found_products = _extract_pks(response.context['results'].object_list)
    assert NEW_BACKEND_FOUND == set(found_products)
    assert EXISTING_PHRASE == response.context['query']


PRODUCTS_TO_UNPUBLISH = {15, 34}


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
                                            client, new_search_backend):
    published_products = NEW_BACKEND_FOUND - PRODUCTS_TO_UNPUBLISH
    EXISTING_PHRASE = 'Group'
    response = client.get(reverse('search:search'), {'q': EXISTING_PHRASE})
    found_products = _extract_pks(response.context['results'].object_list)
    assert published_products == set(found_products)
    assert EXISTING_PHRASE == response.context['query']
