import graphene

from .....tax.models import TaxClass
from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_CLASS_FRAGMENT

QUERY = (
    """
    query TaxClass($id: ID!) {
        taxClass(id: $id) {
            ...TaxClass
        }
    }
    """
    + TAX_CLASS_FRAGMENT
)


def _test_field_resolvers(tax_class: TaxClass, data: dict):
    country_rates = tax_class.country_rates.all()
    country_rate = country_rates[0]
    assert data["id"] == graphene.Node.to_global_id("TaxClass", tax_class.pk)
    assert data["name"] == tax_class.name
    assert len(data["countries"]) == len(country_rates)
    assert country_rate
    assert data["countries"][0]["country"]["code"] == country_rate.country.code
    assert data["countries"][0]["rate"] == country_rate.rate


def test_tax_class_query_no_permissions(user_api_client):
    # given
    tax_class = TaxClass.objects.first()
    id = graphene.Node.to_global_id("TaxClass", tax_class.pk)
    variables = {"id": id}

    # when
    response = user_api_client.post_graphql(QUERY, variables)

    # then
    assert_no_permission(response)


def test_tax_class_query_staff_user(staff_api_client, default_tax_class):
    # given
    tax_class = default_tax_class
    id = graphene.Node.to_global_id("TaxClass", tax_class.pk)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxClass"]
    _test_field_resolvers(tax_class, data)


def test_tax_class_query_app(app_api_client, default_tax_class):
    # given
    tax_class = default_tax_class
    id = graphene.Node.to_global_id("TaxClass", tax_class.pk)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxClass"]
    _test_field_resolvers(tax_class, data)


TAX_CLASS_PRIVATE_METADATA_QUERY = """
    query TaxClass($id: ID!) {
        taxClass(id: $id) {
            id
            privateMetadata {
                key
                value
            }
        }
    }
"""


def test_tax_class_private_metadata_requires_manage_taxes_app(
    app_api_client, default_tax_class, permission_manage_taxes
):
    # given
    tax_class = default_tax_class
    id = graphene.Node.to_global_id("TaxClass", tax_class.pk)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        TAX_CLASS_PRIVATE_METADATA_QUERY,
        variables,
        permissions=[permission_manage_taxes],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxClass"]
    assert data["id"] == graphene.Node.to_global_id("TaxClass", tax_class.pk)
    assert data["privateMetadata"]


def test_tax_class_private_metadata_requires_manage_taxes_staff_user(
    staff_api_client, default_tax_class, permission_manage_taxes
):
    # given
    tax_class = default_tax_class
    id = graphene.Node.to_global_id("TaxClass", tax_class.pk)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        TAX_CLASS_PRIVATE_METADATA_QUERY,
        variables,
        permissions=[permission_manage_taxes],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxClass"]
    assert data["id"] == graphene.Node.to_global_id("TaxClass", tax_class.pk)
    assert data["privateMetadata"]
