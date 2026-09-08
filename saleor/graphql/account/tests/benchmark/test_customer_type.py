import graphene
import pytest

from .....account.models import CustomerType
from ....tests.utils import get_graphql_content

ATTRIBUTE_FRAGMENT = """
    fragment AttributeFields on Attribute {
        slug
        name
        type
        inputType
        choices(first: 10) {
            edges {
                node {
                    name
                    slug
                }
            }
        }
        valueRequired
        visibleInStorefront
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_customer_type(
    customer_type,
    staff_api_client,
    loyalty_customer_attribute,
    hidden_customer_attribute,
    segment_customer_attribute,
    permission_manage_customer_types_and_attributes,
    count_queries,
):
    query = (
        ATTRIBUTE_FRAGMENT
        + """
        query CustomerType($id: ID!) {
            customerType(id: $id) {
                id
                name
                slug
                isDefault
                attributes {
                    ...AttributeFields
                }
                availableAttributes(first: 10) {
                    edges {
                        node {
                            ...AttributeFields
                        }
                    }
                }
            }
        }
    """
    )
    customer_type.customer_attributes.add(
        loyalty_customer_attribute, hidden_customer_attribute
    )
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_customer_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["customerType"]
    assert data


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_customer_types(
    customer_type,
    default_customer_type,
    staff_api_client,
    loyalty_customer_attribute,
    hidden_customer_attribute,
    segment_customer_attribute,
    permission_manage_customer_types_and_attributes,
    count_queries,
):
    query = (
        ATTRIBUTE_FRAGMENT
        + """
        query {
            customerTypes(first: 10) {
                edges {
                    node {
                        id
                        name
                        slug
                        isDefault
                        attributes {
                            ...AttributeFields
                        }
                        availableAttributes(first: 10) {
                            edges {
                                node {
                                    ...AttributeFields
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    )
    extra_customer_types = CustomerType.objects.bulk_create(
        [
            CustomerType(name="Wholesale", slug="wholesale"),
            CustomerType(name="Retail", slug="retail"),
        ]
    )
    customer_type.customer_attributes.add(
        loyalty_customer_attribute, hidden_customer_attribute
    )
    for extra_customer_type in extra_customer_types:
        extra_customer_type.customer_attributes.add(
            loyalty_customer_attribute, segment_customer_attribute
        )
    response = staff_api_client.post_graphql(
        query,
        {},
        permissions=[permission_manage_customer_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["customerTypes"]
    assert data
