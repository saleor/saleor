import graphene
import pytest

from .....tax.models import TaxClass
from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_CLASS_FRAGMENT

QUERY = (
    """
    query TaxClasses($sortBy: TaxClassSortingInput, $filter: TaxClassFilterInput) {
        taxClasses(first: 100, sortBy: $sortBy, filter: $filter) {
            totalCount
            edges {
                node {
                    ...TaxClass
                }
            }
        }
    }
    """
    + TAX_CLASS_FRAGMENT
)


def test_tax_classes_query_no_permissions(user_api_client):
    # when
    response = user_api_client.post_graphql(QUERY, {}, permissions=[])

    # then
    assert_no_permission(response)


def test_tax_classes_query_staff_user(staff_api_client):
    # given
    total_count = TaxClass.objects.count()

    # when
    response = staff_api_client.post_graphql(QUERY, {})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["taxClasses"]["edges"]
    assert content["data"]["taxClasses"]["totalCount"] == total_count
    assert len(edges) == total_count
    assert edges[0]["node"]


def test_tax_classes_query_app(app_api_client):
    # given
    total_count = TaxClass.objects.count()

    # when
    response = app_api_client.post_graphql(QUERY, {})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["taxClasses"]["edges"]
    assert content["data"]["taxClasses"]["totalCount"] == total_count
    assert len(edges) == total_count
    assert edges[0]["node"]


def test_tax_classes_filter_by_ids(staff_api_client):
    # given
    id = graphene.Node.to_global_id("TaxClass", TaxClass.objects.first().pk)
    ids = [id]

    # when
    response = staff_api_client.post_graphql(QUERY, {"filter": {"ids": ids}})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["taxClasses"]["edges"]
    assert len(edges) == 1
    assert edges[0]["node"]["id"] == id


@pytest.mark.parametrize(("country", "count"), [("PL", 1), ("US", 0)])
def test_tax_classes_filter_by_countries(country, count, staff_api_client):
    # given
    filter = {"filter": {"countries": [country]}}

    # when
    response = staff_api_client.post_graphql(QUERY, filter)

    # then
    content = get_graphql_content(response)
    edges = content["data"]["taxClasses"]["edges"]
    assert len(edges) == count
