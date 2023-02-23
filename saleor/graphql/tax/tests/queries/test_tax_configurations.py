import graphene

from .....tax.models import TaxConfiguration
from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_CONFIGURATION_FRAGMENT

QUERY = (
    """
    query TaxConfiguration($filter: TaxConfigurationFilterInput) {
        taxConfigurations(first: 100, filter: $filter) {
            totalCount
            edges {
                node {
                    ...TaxConfiguration
                }
            }
        }
    }
    """
    + TAX_CONFIGURATION_FRAGMENT
)


def test_tax_configurations_query_no_permissions(channel_USD, user_api_client):
    # when
    response = user_api_client.post_graphql(QUERY, {}, permissions=[])

    # then
    assert_no_permission(response)


def test_tax_configurations_query_staff_user(channel_USD, staff_api_client):
    # given
    total_count = TaxConfiguration.objects.count()

    # when
    response = staff_api_client.post_graphql(QUERY, {})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["taxConfigurations"]["edges"]
    assert content["data"]["taxConfigurations"]["totalCount"] == total_count
    assert len(edges) == total_count
    assert edges[0]["node"]


def test_tax_configurations_query_app(channel_USD, app_api_client):
    # given
    total_count = TaxConfiguration.objects.count()

    # when
    response = app_api_client.post_graphql(QUERY, {})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["taxConfigurations"]["edges"]
    assert content["data"]["taxConfigurations"]["totalCount"] == total_count
    assert len(edges) == total_count
    assert edges[0]["node"]


def test_tax_configurations_filter(channel_USD, staff_api_client):
    # given
    id = graphene.Node.to_global_id(
        "TaxConfiguration", TaxConfiguration.objects.first().pk
    )
    ids = [id]

    # when
    response = staff_api_client.post_graphql(QUERY, {"ids": ids})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["taxConfigurations"]["edges"]
    assert len(edges) == 1
    assert edges[0]["node"]["id"] == id
