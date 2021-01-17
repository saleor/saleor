import graphene
import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_page_type(
    page_type,
    staff_api_client,
    author_page_attribute,
    permission_manage_pages,
    permission_manage_products,
    count_queries,
):
    query = """
        query PageType($id: ID!, $filters: AttributeFilterInput) {
            pageType(id: $id) {
                id
                name
                slug
                hasPages
                attributes {
                    slug
                    name
                    type
                    inputType
                    values {
                        name
                        slug
                    }
                    valueRequired
                    visibleInStorefront
                    filterableInStorefront
                }
                availableAttributes(first: 10, filter: $filters) {
                    edges {
                        node {
                            slug
                            name
                            type
                            inputType
                            values {
                                name
                                slug
                            }
                            valueRequired
                            visibleInStorefront
                            filterableInStorefront
                        }
                    }
                }
            }
        }
    """
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products, permission_manage_pages],
    )
    content = get_graphql_content(response)
    data = content["data"]["pageType"]
    assert data


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_page_types(
    page_type_list,
    staff_api_client,
    author_page_attribute,
    permission_manage_pages,
    permission_manage_products,
    count_queries,
):
    query = """
        query {
            pageTypes(first: 10) {
                edges {
                    node {
                        id
                        name
                        slug
                        hasPages
                        attributes {
                            slug
                            name
                            type
                            inputType
                            values {
                                name
                                slug
                            }
                            valueRequired
                            visibleInStorefront
                            filterableInStorefront
                        }
                        availableAttributes(first: 10) {
                            edges {
                                node {
                                    slug
                                    name
                                    type
                                    inputType
                                    values {
                                        name
                                        slug
                                    }
                                    valueRequired
                                    visibleInStorefront
                                    filterableInStorefront
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    response = staff_api_client.post_graphql(
        query,
        {},
        permissions=[permission_manage_products, permission_manage_pages],
    )
    content = get_graphql_content(response)
    data = content["data"]["pageTypes"]
    assert data
