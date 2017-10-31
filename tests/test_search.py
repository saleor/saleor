from saleor.product.models import Product
from django.core.management import call_command
from django.core.urlresolvers import reverse

from decimal import Decimal
import pytest

MATCH_SEARCH_REQUEST = ['method', 'host', 'port', 'path', 'body']
PRODUCTS_FOUND = [41, 59]  # same as in recorded data!
DATE_OF_RECORDING = '2017-10-18'


@pytest.fixture(scope='function', autouse=True)
def recorded_on_date(freezer):
    '''Freeze date during tests to date of recording

    Current date is used in search query, please change used constant to new
    current date when re-recording communication with live elasticsearch.
    Leave changed date as new fixed time.
    '''
    freezer.move_to(DATE_OF_RECORDING)


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once')
def test_index_products(product_list):
    options = {'backend_name': 'default'}
    call_command('update_index', **options)


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_search_with_empty_result(db, client):
    WORD = 'foo'
    response = client.get(reverse('search:search'), {'q': WORD})
    assert 0 == len(response.context['results'].object_list)
    assert WORD == response.context['query']


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_search_multiple_words(db, client):
    ''' Check request format for multiple word phrases '''
    PHRASE = 'how fortunate the man with none'
    client.get(reverse('search:search'), {'q': PHRASE})


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
    return [gen_product_with_id(prod) for prod in PRODUCTS_FOUND]


def _extract_pks(object_list):
    return [prod.pk for prod, _ in object_list]


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_search_with_result(db, indexed_products, client):
    EXISTING_PHRASE = 'Group'
    response = client.get(reverse('search:search'), {'q': EXISTING_PHRASE})
    found_products = _extract_pks(response.context['results'].object_list)
    assert PRODUCTS_FOUND == sorted(found_products)
    assert EXISTING_PHRASE == response.context['query']


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
    WORD = 'foo'
    response = client.get(reverse('search:search'), {'q': WORD})
    assert 0 == len(response.context['results'].object_list)
    assert WORD == response.context['query']


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_results(db, client, new_search_backend):
    WORD = 'group'
    response = client.get(reverse('search:search'), {'q': WORD})
    _extract_pks(response.context['results'].object_list)
