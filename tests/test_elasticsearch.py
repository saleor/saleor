import pytest
from django.urls import reverse
from elasticsearch_dsl.connections import connections
from prices import Money

from saleor.product.models import Product

MATCH_SEARCH_REQUEST = ["method", "host", "port", "path"]
STOREFRONT_PRODUCTS = {15, 56}  # same as in recorded data!
DASHBOARD_PRODUCTS = {58, 56}
PRODUCTS_INDEXED = STOREFRONT_PRODUCTS | DASHBOARD_PRODUCTS
PRODUCTS_TO_UNPUBLISH = {56}  # choose from PRODUCTS_INDEXED
PHRASE_WITH_RESULTS = "Group"
PHRASE_WITHOUT_RESULTS = "foo"

ES_URL = "http://search:9200"  # make it real for communication recording


@pytest.fixture(scope="module", autouse=True)
def elasticsearch_connection():
    connections.create_connection("default", hosts=[ES_URL])


@pytest.fixture(scope="function", autouse=True)
def elasticsearch_enabled(settings):
    settings.ES_URL = ES_URL
    settings.ENABLE_SEARCH = True
    settings.SEARCH_BACKEND = "saleor.search.backends.elasticsearch"


@pytest.fixture(scope="function", autouse=True)
def elasticsearch_autosync_disabled(settings):
    """Prevent ES index from being refreshed every time objects are saved."""
    settings.ELASTICSEARCH_DSL_AUTO_REFRESH = False
    settings.ELASTICSEARCH_DSL_AUTOSYNC = False


@pytest.mark.vcr()
@pytest.fixture
def indexed_products(product_type, category):
    """Products to be found by search backend.

    We need existing objects with primary keys same as search service
    returned in response. Otherwise search view won't find anything.
    Purpose of this fixture is for integration with search service only!
    pks must be in response in appropiate recorded cassette.
    """

    def gen_product_with_id(object_id):
        product = Product.objects.create(
            pk=object_id,
            name="Test product " + str(object_id),
            price=Money(10, "USD"),
            product_type=product_type,
            category=category,
            is_published=True,
        )
        return product

    return [gen_product_with_id(prod) for prod in PRODUCTS_INDEXED]


def execute_search(client, phrase):
    response = client.get(reverse("search:search"), {"q": phrase})
    assert phrase == response.context["query"]
    found_objs = response.context["results"].object_list
    return [prod.pk for prod, _ in found_objs]


@pytest.mark.integration
@pytest.mark.vcr(record_mode="once", match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_empty_results(db, client):
    assert 0 == len(execute_search(client, PHRASE_WITHOUT_RESULTS))


@pytest.mark.integration
@pytest.mark.vcr(record_mode="once", match_on=MATCH_SEARCH_REQUEST)
def test_new_search_with_result(db, indexed_products, client):
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
@pytest.mark.vcr(record_mode="once", match_on=MATCH_SEARCH_REQUEST)
def test_new_search_doesnt_show_unpublished(db, products_with_mixed_publishing, client):
    published_products = STOREFRONT_PRODUCTS - PRODUCTS_TO_UNPUBLISH
    found_products = execute_search(client, PHRASE_WITH_RESULTS)
    assert published_products == set(found_products)
