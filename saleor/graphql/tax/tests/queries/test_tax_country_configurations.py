from saleor.tax.models import TaxClassCountryRate

from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_COUNTRY_CONFIGURATION_FRAGMENT

QUERY = (
    """
    query TaxCountryConfigurations {
        taxCountryConfigurations {
            ...TaxCountryConfiguration
        }
    }
    """
    + TAX_COUNTRY_CONFIGURATION_FRAGMENT
)


def _test_field_resolvers(data: dict):
    configured_countries = set(TaxClassCountryRate.objects.values_list("country"))
    assert len(data["taxCountryConfigurations"]) == len(configured_countries)


def test_tax_country_configurations_query_no_permissions(user_api_client):
    # when
    response = user_api_client.post_graphql(QUERY, {}, permissions=[])

    # then
    assert_no_permission(response)


def test_tax_country_configurations_query_staff_user(staff_api_client):
    # when
    response = staff_api_client.post_graphql(QUERY, {})

    # then
    content = get_graphql_content(response)
    _test_field_resolvers(content["data"])


def test_tax_country_configurations_query_app(app_api_client):
    # when
    response = app_api_client.post_graphql(QUERY, {})

    # then
    content = get_graphql_content(response)
    _test_field_resolvers(content["data"])
