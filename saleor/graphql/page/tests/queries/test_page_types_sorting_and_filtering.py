import graphene
import pytest

from .....page.models import PageType
from ....tests.utils import get_graphql_content

PAGE_TYPES_QUERY = """
    query PageTypes($filter: PageTypeFilterInput, $sortBy: PageTypeSortingInput) {
        pageTypes(first: 10, filter: $filter, sortBy: $sortBy) {
            edges {
                node {
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "search_value, result_items",
    [("test", [0]), ("page", [0, 1, 2]), ("Example page", [1, 2])],
)
def test_filter_page_types(
    search_value, result_items, staff_api_client, page_type_list
):
    # given
    variables = {"filter": {"search": search_value}}

    # when
    response = staff_api_client.post_graphql(PAGE_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypes"]["edges"]

    assert {node["node"]["id"] for node in data} == {
        graphene.Node.to_global_id("PageType", page_type_list[i].pk)
        for i in result_items
    }


@pytest.mark.parametrize(
    "filter_by, pages_count",
    [
        ({"slugs": ["page-type-2", "page-type-3"]}, 2),
        ({"slugs": []}, 3),
    ],
)
def test_filter_page_types_filtering(
    filter_by, pages_count, staff_api_client, page_type_list
):
    # given
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        PAGE_TYPES_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pageTypes"]["edges"]
    assert len(pages_nodes) == pages_count


@pytest.mark.parametrize(
    "direction, order_direction",
    (("ASC", "name"), ("DESC", "-name")),
)
def test_sort_page_types_by_name(
    direction, order_direction, staff_api_client, page_type_list
):
    # given
    variables = {"sortBy": {"field": "NAME", "direction": direction}}

    # when
    response = staff_api_client.post_graphql(PAGE_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypes"]["edges"]

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("PageType", page_type.pk)
        for page_type in PageType.objects.order_by(order_direction)
    ]


@pytest.mark.parametrize(
    "direction, order_direction",
    (("ASC", "slug"), ("DESC", "-slug")),
)
def test_sort_page_types_by_slug(
    direction, order_direction, staff_api_client, page_type_list
):
    # given
    variables = {"sortBy": {"field": "SLUG", "direction": direction}}

    # when
    response = staff_api_client.post_graphql(PAGE_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypes"]["edges"]

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("PageType", page_type.pk)
        for page_type in PageType.objects.order_by(order_direction)
    ]


@pytest.mark.parametrize(
    "direction, result_items",
    (("ASC", [1, 2]), ("DESC", [2, 1])),
)
def test_filter_and_sort_by_slug_page_types(
    direction, result_items, staff_api_client, page_type_list
):
    # given
    variables = {
        "filter": {"search": "Example"},
        "sortBy": {"field": "SLUG", "direction": direction},
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypes"]["edges"]

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("PageType", page_type_list[i].pk)
        for i in result_items
    ]
