from saleor.product.models import Product
from saleor.userprofile.models import User
from django.core.urlresolvers import reverse
from elasticsearch_dsl.connections import connections
from decimal import Decimal
import pytest

MATCH_SEARCH_REQUEST = ['method', 'host', 'port', 'path', 'body']
STOREFRONT_PRODUCTS = {15, 56}  # same as in recorded data!
DASHBOARD_PRODUCTS = {6, 29}
PRODUCTS_INDEXED = STOREFRONT_PRODUCTS | DASHBOARD_PRODUCTS
PRODUCTS_TO_UNPUBLISH = {56}  # choose from PRODUCTS_INDEXED
PHRASE_WITH_RESULTS = 'Group'
PHRASE_WITHOUT_RESULTS = 'foo'


@pytest.fixture(scope='function', autouse=True)
def es_autosync_disabled(settings):
    ''' Prevent ES index from being refreshed every time obj is saved '''
    settings.ELASTICSEARCH_DSL_AUTO_REFRESH = False
    settings.ELASTICSEARCH_DSL_AUTOSYNC = False


@pytest.fixture(scope='module', autouse=True)
def enable_es():
    ES_URL = 'http://search:9200'
    connections.create_connection('default', hosts=[ES_URL])


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
    assert 0 == len(execute_search(client, PHRASE_WITHOUT_RESULTS))


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_result(db, indexed_products, client):
    ''' some products founds, only those both in search result and objects '''
    found_products = execute_search(client, PHRASE_WITH_RESULTS)
    assert STOREFRONT_PRODUCTS == set(found_products)


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
    published_products = STOREFRONT_PRODUCTS - PRODUCTS_TO_UNPUBLISH
    found_products = execute_search(client, PHRASE_WITH_RESULTS)
    assert published_products == set(found_products)


def execute_dashboard_search(client, phrase):
    response = client.get(reverse('dashboard:search'), {'q': phrase})
    assert phrase == response.context['query']
    found_prod = {p.pk for p in response.context['products']}
    found_users = {p.pk for p in response.context['users']}
    found_orders = {p.pk for p in response.context['orders']}
    return found_prod, found_users, found_orders


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_dashboard_search_with_empty_results(db, admin_client):
    ''' no products found with foo '''
    products, users, orders = execute_dashboard_search(admin_client,
                                                       PHRASE_WITHOUT_RESULTS)
    assert 0 == len(products)
    assert 0 == len(users)
    assert 0 == len(orders)


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_dashboard_search_with_product_result(db, indexed_products,
                                              admin_client):
    ''' products found in dashboard search view  '''
    products, _, _ = execute_dashboard_search(admin_client,
                                              PHRASE_WITH_RESULTS)
    assert DASHBOARD_PRODUCTS == products


EXISTING_EMAIL = 'amy.smith@example.com'
USERS = {EXISTING_EMAIL: 9}


@pytest.fixture
def customers(db):
    for email, pk in USERS.items():
        User.objects.create_user(email, 'password', pk=pk)


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_dashboard_search_user_by_email(db, admin_client, customers):
    ''' user can be found in dashboard search by email address '''
    _, users, _ = execute_dashboard_search(admin_client, EXISTING_EMAIL)
    assert 1 == len(users)
    assert USERS[EXISTING_EMAIL] in users
