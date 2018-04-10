from decimal import Decimal

import pytest
from django.urls import reverse
from elasticsearch_dsl.connections import connections

from saleor.account.models import User
from saleor.order.models import Order
from saleor.product.models import Product

MATCH_SEARCH_REQUEST = ['method', 'host', 'port', 'path']
STOREFRONT_PRODUCTS = {15, 56}  # same as in recorded data!
DASHBOARD_PRODUCTS = {58, 56}
PRODUCTS_INDEXED = STOREFRONT_PRODUCTS | DASHBOARD_PRODUCTS
PRODUCTS_TO_UNPUBLISH = {56}  # choose from PRODUCTS_INDEXED
PHRASE_WITH_RESULTS = 'Group'
PHRASE_WITHOUT_RESULTS = 'foo'

ES_URL = 'http://search:9200'  # make it real for communication recording


@pytest.fixture(scope='module', autouse=True)
def elasticsearch_connection():
    connections.create_connection('default', hosts=[ES_URL])


@pytest.fixture(scope='function', autouse=True)
def elasticsearch_enabled(settings):
    settings.ES_URL = ES_URL
    settings.ENABLE_SEARCH = True
    settings.SEARCH_BACKEND = 'saleor.search.backends.elasticsearch'


@pytest.fixture(scope='function', autouse=True)
def elasticsearch_autosync_disabled(settings):
    """Prevent ES index from being refreshed every time objects are saved."""
    settings.ELASTICSEARCH_DSL_AUTO_REFRESH = False
    settings.ELASTICSEARCH_DSL_AUTOSYNC = False


@pytest.mark.vcr()
@pytest.fixture
def indexed_products(product_type, default_category):
    """Products to be found by search backend.

    We need existing objects with primary keys same as search service
    returned in response. Otherwise search view won't find anything.
    Purpose of this fixture is for integration with search service only!
    pks must be in response in appropiate recorded cassette.
    """
    def gen_product_with_id(object_id):
        product = Product.objects.create(
            pk=object_id,
            name='Test product ' + str(object_id),
            price=Decimal(10.0),
            product_type=product_type,
            category=default_category)
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
    assert 0 == len(execute_search(client, PHRASE_WITHOUT_RESULTS))


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_result(db, indexed_products, client):
    found_products = execute_search(client, PHRASE_WITH_RESULTS)
    assert STOREFRONT_PRODUCTS == set(found_products)


@pytest.fixture
def products_with_mixed_publishing(indexed_products):
    products_to_unpublish = Product.objects.filter(
        pk__in=PRODUCTS_TO_UNPUBLISH)
    for prod in products_to_unpublish:
        prod.is_published = False
        prod.save()
    return indexed_products


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_new_search_doesnt_show_unpublished(
        db, products_with_mixed_publishing, client):
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
    products, users, orders = execute_dashboard_search(
        admin_client, PHRASE_WITHOUT_RESULTS)
    assert 0 == len(products)
    assert 0 == len(users)
    assert 0 == len(orders)


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_dashboard_search_with_product_result(
        db, indexed_products, admin_client):
    products, _, _ = execute_dashboard_search(admin_client,
                                              PHRASE_WITH_RESULTS)
    assert DASHBOARD_PRODUCTS == products


# data below must be aligned with recorded communication every time
EXISTING_EMAIL = 'nancy.mccoy@example.com'
NON_EXISTING_EMAIL = 'john.doe@foo.bar'
USER_WITH_ORDER = 'jennifer.green@example.com'
EXISTING_NAME = 'Rhonda'
EXISTING_NAME_FULL = 'rhonda.ayala@example.com'
USERS = {EXISTING_EMAIL: 9,
         NON_EXISTING_EMAIL: 870,
         USER_WITH_ORDER: 666,
         EXISTING_NAME_FULL: 6}
ORDERS = {USER_WITH_ORDER: {18, 19}}


@pytest.fixture
def customers(db):
    for email, pk in USERS.items():
        User.objects.create_user(email, 'password', pk=pk)


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_dashboard_search_user_by_email(db, admin_client, customers):
    _, users, _ = execute_dashboard_search(admin_client, EXISTING_EMAIL)
    assert {USERS[EXISTING_EMAIL]} == users


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_dashboard_search_user_name(db, admin_client, customers):
    _, users, _ = execute_dashboard_search(admin_client, EXISTING_NAME)
    assert USERS[EXISTING_NAME_FULL] in users


@pytest.fixture
def orders(db, address):
    all_pks = set()
    for email, pks in ORDERS.items():
        for pk in pks:
            Order.objects.create(
                billing_address=address, user_email=email, pk=pk)
        all_pks = all_pks | pks
    return all_pks


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once', match_on=MATCH_SEARCH_REQUEST)
def test_dashboard_search_orders_by_user(db, admin_client, customers, orders):
    _, _, orders = execute_dashboard_search(admin_client, USER_WITH_ORDER)
    assert ORDERS[USER_WITH_ORDER] == orders
