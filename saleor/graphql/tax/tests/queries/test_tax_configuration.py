import graphene

from saleor.tax.models import TaxConfiguration

from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_CONFIGURATION_FRAGMENT

QUERY = (
    """
    query TaxConfiguration($id: ID!) {
        taxConfiguration(id: $id) {
            ...TaxConfiguration
        }
    }
    """
    + TAX_CONFIGURATION_FRAGMENT
)


def _test_field_resolvers(tax_configuration: TaxConfiguration, data: dict):
    country_exceptions = tax_configuration.country_exceptions.all()
    country_exception = country_exceptions[0]
    assert data["id"] == graphene.Node.to_global_id(
        "TaxConfiguration", tax_configuration.pk
    )
    assert data["chargeTaxes"] == tax_configuration.charge_taxes
    assert data["displayGrossPrices"] == tax_configuration.display_gross_prices
    assert data["pricesEnteredWithTax"] == tax_configuration.prices_entered_with_tax
    assert len(data["countries"]) == len(country_exceptions)
    assert data["countries"][0]["country"]["code"] == country_exception.country.code
    assert data["countries"][0]["chargeTaxes"] == country_exception.charge_taxes
    assert (
        data["countries"][0]["displayGrossPrices"]
        == country_exception.display_gross_prices
    )


def test_tax_configuration_query_no_permissions(channel_USD, staff_api_client):
    # given
    id = graphene.Node.to_global_id(
        "TaxConfiguration", channel_USD.tax_configuration.pk
    )
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(QUERY, variables, permissions=[])

    # then
    assert_no_permission(response)


def test_tax_configuration_query_staff_user(
    channel_USD, staff_api_client, permission_manage_taxes
):
    # given
    id = graphene.Node.to_global_id(
        "TaxConfiguration", channel_USD.tax_configuration.pk
    )
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    _test_field_resolvers(
        channel_USD.tax_configuration, content["data"]["taxConfiguration"]
    )


def test_tax_configuration_query_app(
    channel_USD, app_api_client, permission_manage_taxes
):
    # given
    id = graphene.Node.to_global_id(
        "TaxConfiguration", channel_USD.tax_configuration.pk
    )
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    _test_field_resolvers(
        channel_USD.tax_configuration, content["data"]["taxConfiguration"]
    )
