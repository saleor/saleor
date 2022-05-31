import graphene

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
    assert content["data"]["taxConfiguration"]["id"] == id


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
    assert content["data"]["taxConfiguration"]["id"] == id
