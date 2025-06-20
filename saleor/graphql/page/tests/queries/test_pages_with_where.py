import graphene
import pytest

from .....page.models import Page, PageType
from ....tests.utils import get_graphql_content

QUERY_PAGES_WITH_WHERE = """
    query ($where: PageWhereInput) {
        pages(first: 5, where:$where) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("where", "pages_count"),
    [
        ({"slug": {"eq": "test-url-1"}}, 1),
        ({"slug": {"oneOf": ["test-url-1", "test-url-2"]}}, 2),
    ],
)
def test_pages_with_where_slug(where, pages_count, staff_api_client, page_list):
    # given
    variables = {"where": where}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_count


def test_pages_with_where_page_type_eq(staff_api_client, page_type_list):
    # given
    page = Page.objects.first()
    assigned_page_type = page.page_type
    page_type_id = graphene.Node.to_global_id("PageType", page.page_type.pk)

    pages_for_page_type = Page.objects.filter(page_type=assigned_page_type).count()
    assert PageType.objects.exclude(pk=assigned_page_type.pk).count() != 0
    assert pages_for_page_type != 0

    variables = {"where": {"pageType": {"eq": page_type_id}}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_for_page_type


def test_pages_with_where_page_type_one_of(staff_api_client, page_type_list):
    # given
    page = Page.objects.first()
    assigned_page_type = page.page_type
    page_type_id = graphene.Node.to_global_id("PageType", page.page_type.pk)

    pages_for_page_type = Page.objects.filter(page_type=assigned_page_type).count()
    assert PageType.objects.exclude(pk=assigned_page_type.pk).count() != 0
    assert pages_for_page_type != 0

    variables = {"where": {"pageType": {"oneOf": [page_type_id]}}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_for_page_type


@pytest.mark.parametrize(
    ("metadata", "expected_indexes"),
    [
        ({"key": "foo"}, [0, 1]),
        ({"key": "foo", "value": {"eq": "bar"}}, [0]),
        ({"key": "foo", "value": {"eq": "baz"}}, []),
        ({"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}, [0, 1]),
        ({"key": "notfound"}, []),
        ({"key": "foo", "value": {"eq": None}}, []),
        ({"key": "foo", "value": {"oneOf": []}}, []),
        (None, []),
    ],
)
def test_pages_with_where_metadata(
    metadata,
    expected_indexes,
    page_list,
    page_type,
    staff_api_client,
):
    # given
    page_list[0].metadata = {"foo": "bar"}
    page_list[1].metadata = {"foo": "zaz"}
    Page.objects.bulk_update(page_list, ["metadata"])
    page_list.append(
        Page.objects.create(
            title="Test page",
            slug="test-url-3",
            is_published=True,
            page_type=page_type,
            metadata={},
        )
    )

    variables = {"where": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages = content["data"]["pages"]["edges"]
    assert len(pages) == len(expected_indexes)
    ids = {node["node"]["id"] for node in pages}
    assert ids == {
        graphene.Node.to_global_id("Page", page_list[i].pk) for i in expected_indexes
    }


def test_pages_query_with_where_by_ids(
    staff_api_client, permission_manage_pages, page_list, page_list_unpublished
):
    query = QUERY_PAGES_WITH_WHERE

    page_ids = [
        graphene.Node.to_global_id("Page", page.pk)
        for page in [page_list[0], page_list_unpublished[-1]]
    ]
    variables = {"where": {"ids": page_ids}}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == len(page_ids)
