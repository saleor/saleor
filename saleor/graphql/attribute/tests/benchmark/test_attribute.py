import graphene
import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_attribute(
    staff_api_client,
    color_attribute,
    permission_manage_products,
    count_queries,
):
    query = """
        query($id: ID!) {
            attribute(id: $id) {
                id
                slug
                name
                inputType
                type
                values {
                    slug
                    inputType
                }
                valueRequired
                visibleInStorefront
                filterableInStorefront
                filterableInDashboard
                availableInGrid
                storefrontSearchPosition
            }
        }
        """
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    response = staff_api_client.post_graphql(query, {"id": attribute_gql_id})

    content = get_graphql_content(response)
    data = content["data"]["attribute"]
    assert data


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_attributes(
    staff_api_client,
    size_attribute,
    weight_attribute,
    color_attribute,
    permission_manage_products,
    count_queries,
):
    query = """
        query {
            attributes(first: 20) {
                edges {
                    node {
                        id
                        slug
                        name
                        inputType
                        type
                        values {
                            slug
                            inputType
                        }
                        valueRequired
                        visibleInStorefront
                        filterableInStorefront
                        filterableInDashboard
                        availableInGrid
                        storefrontSearchPosition
                    }
                }
            }
        }
        """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    response = staff_api_client.post_graphql(query, {})

    content = get_graphql_content(response)
    data = content["data"]["attributes"]
    assert data
