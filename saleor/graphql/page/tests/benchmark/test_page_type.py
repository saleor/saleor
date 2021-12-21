import graphene
import pytest

from .....page.models import PageType
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
                    filterableInStorefront
                }
                availableAttributes(first: 10, filter: $filters) {
                    edges {
                        node {
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
                            filterableInStorefront
                        }
                        availableAttributes(first: 10) {
                            edges {
                                node {
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_page_types_for_federation_query_count(
    api_client,
    django_assert_num_queries,
    count_queries,
):
    page_types = PageType.objects.bulk_create(
        [
            PageType(name="type 1", slug="type-1"),
            PageType(name="type 2", slug="type-2"),
            PageType(name="type 3", slug="type-3"),
        ]
    )

    query = """
        query GetAppInFederation($representations: [_Any]) {
            _entities(representations: $representations) {
                __typename
                ... on PageType {
                    id
                    name
                }
            }
        }
    """

    variables = {
        "representations": [
            {
                "__typename": "PageType",
                "id": graphene.Node.to_global_id("PageType", page_types[0].pk),
            },
        ],
    }

    with django_assert_num_queries(1):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 1

    variables = {
        "representations": [
            {
                "__typename": "PageType",
                "id": graphene.Node.to_global_id("PageType", page_type.pk),
            }
            for page_type in page_types
        ],
    }

    with django_assert_num_queries(1):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 3
